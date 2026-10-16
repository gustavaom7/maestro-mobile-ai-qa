import json
from types import SimpleNamespace

import pytest

import generate_flow as gf

VALID_FLOW = """appId: org.wikipedia
---
# Open the app
- launchApp
- tapOn: "Search Wikipedia"
- inputText: "Maestro"
- assertVisible: "Maestro"
"""


class FakeMessages:
    def __init__(self, text, stop_reason="end_turn", input_tokens=100, output_tokens=50):
        self.text = text
        self.stop_reason = stop_reason
        self.usage = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.text)],
            stop_reason=self.stop_reason,
            usage=self.usage,
        )


def fake_client(text=VALID_FLOW, **kwargs):
    return SimpleNamespace(messages=FakeMessages(text, **kwargs))


def test_returns_validated_flow_and_usage():
    client = fake_client()
    flow, usage = gf.generate_flow(client, "org.wikipedia", "search for Maestro")
    assert flow == VALID_FLOW.strip()
    assert (usage.input_tokens, usage.output_tokens) == (100, 50)
    call = client.messages.calls[0]
    assert call["model"] == gf.DEFAULT_MODEL
    assert "org.wikipedia" in call["messages"][0]["content"]


def test_strips_markdown_fence():
    client = fake_client("```yaml\n" + VALID_FLOW + "```")
    flow, _ = gf.generate_flow(client, "org.wikipedia", "x")
    assert flow.startswith("appId: org.wikipedia")


@pytest.mark.parametrize(
    "text, reason",
    [
        ("- launchApp\n", "expected a header"),
        ("name: x\n---\n- launchApp\n", "no appId"),
        ("appId: com.other\n---\n- launchApp\n", "expected 'org.wikipedia'"),
        ("appId: org.wikipedia\n---\n[]\n", "empty"),
        ("appId: org.wikipedia\n---\n- 42\n", "command 1"),
        ("appId: org.wikipedia\n---\n- tapOn: [unclosed\n", "not valid YAML"),
    ],
)
def test_rejects_invalid_flows(text, reason):
    with pytest.raises(gf.GenerationError, match=reason):
        gf.generate_flow(fake_client(text), "org.wikipedia", "x")


def test_rejects_truncated_answer():
    with pytest.raises(gf.GenerationError, match="cut off"):
        gf.generate_flow(fake_client(stop_reason="max_tokens"), "org.wikipedia", "x")


def test_rejects_refusal():
    with pytest.raises(gf.GenerationError, match="declined"):
        gf.generate_flow(fake_client(stop_reason="refusal"), "org.wikipedia", "x")


def test_cost_uses_price_table():
    usage = gf.Usage(input_tokens=1_000_000, output_tokens=1_000_000)
    assert usage.cost_usd("claude-sonnet-4-6") == pytest.approx(18.0)
    assert usage.cost_usd("unknown-model") is None


def test_main_writes_flow_copy_and_log(tmp_path, monkeypatch):
    monkeypatch.setattr(gf, "GENERATED_DIR", tmp_path / "generated")
    monkeypatch.setattr(gf, "LOG_FILE", tmp_path / "generations.jsonl")
    output = tmp_path / "flows" / "11_search.yaml"

    code = gf.main(["--app-id", "org.wikipedia", "--scenario", "search", "--output", str(output)],
                   client=fake_client())

    assert code == 0
    assert output.read_text() == VALID_FLOW.strip() + "\n"
    assert (tmp_path / "generated" / "11_search.yaml").read_text() == output.read_text()
    entry = json.loads((tmp_path / "generations.jsonl").read_text().splitlines()[0])
    assert entry["output_tokens"] == 50
    assert entry["cost_usd"] == pytest.approx((100 * 3 + 50 * 15) / 1_000_000)


def test_main_does_not_write_an_unusable_flow(tmp_path, capsys):
    output = tmp_path / "bad.yaml"
    code = gf.main(["--app-id", "org.wikipedia", "--scenario", "x", "--output", str(output)],
                   client=fake_client("not a flow"))
    assert code == 2
    assert not output.exists()
    assert "unusable flow" in capsys.readouterr().err
