"""
Generate a Maestro flow (YAML) from a plain-language scenario, using the
Anthropic API.

Goal: speed up writing test cases with an LLM without turning it into a black
box. The script validates the generated YAML, prints it for human review, and
keeps an untouched copy plus a log entry (tokens, cost) so the edits made
before the flow passes can be measured later with measure_edits.py.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    python generate_flow.py \
        --app-id org.wikipedia \
        --scenario "Open the app, search for 'Test automation' and check that the first result shows" \
        --output ../../maestro/mobile/flows/11_generated_search.yaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2000

HERE = Path(__file__).resolve().parent
GENERATED_DIR = HERE / "generated"
LOG_FILE = HERE / "generations.jsonl"

# USD per million tokens (input, output), Anthropic first-party API rates.
PRICES_PER_MTOK = {
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

SYSTEM_PROMPT = """You are a QA engineer who specializes in Maestro
(https://maestro.mobile.dev). Output ONLY a valid Maestro YAML flow, with no
explanation, no markdown and no backticks. The YAML must start with the
header "appId: <app_id>", then "---", then the list of commands. Use only
official Maestro commands (launchApp, tapOn, inputText, assertVisible,
takeScreenshot, back, scroll, swipe, etc). Prefer selectors by id or visible
text over fixed coordinates, and add a short comment above each logical block
of the test explaining its intent."""

FENCE = re.compile(r"^```[a-zA-Z]*\s*\n(.*?)\n```\s*$", re.DOTALL)


class GenerationError(Exception):
    """The model's answer cannot be used as a flow."""


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int

    def cost_usd(self, model: str) -> float | None:
        prices = PRICES_PER_MTOK.get(model)
        if prices is None:
            return None
        price_in, price_out = prices
        return (self.input_tokens * price_in + self.output_tokens * price_out) / 1_000_000


def strip_fences(text: str) -> str:
    """Remove a markdown code fence if the model added one despite the prompt."""
    text = text.strip()
    match = FENCE.match(text)
    return match.group(1).strip() if match else text


def validate_flow(flow_yaml: str, app_id: str) -> None:
    """Raise GenerationError unless the text is a Maestro flow for app_id."""
    try:
        docs = list(yaml.safe_load_all(flow_yaml))
    except yaml.YAMLError as exc:
        raise GenerationError(f"not valid YAML: {exc}") from exc

    if len(docs) != 2:
        raise GenerationError(f"expected a header and a command list separated by '---', got {len(docs)} document(s)")
    header, commands = docs
    if not isinstance(header, dict) or "appId" not in header:
        raise GenerationError("header has no appId")
    if header["appId"] != app_id:
        raise GenerationError(f"appId is {header['appId']!r}, expected {app_id!r}")
    if not isinstance(commands, list) or not commands:
        raise GenerationError("command list is empty")
    for i, command in enumerate(commands, start=1):
        if not isinstance(command, (str, dict)):
            raise GenerationError(f"command {i} is not a Maestro command: {command!r}")


def generate_flow(client, app_id: str, scenario: str, model: str = DEFAULT_MODEL) -> tuple[str, Usage]:
    """Ask the model for a flow and return (validated YAML, token usage)."""
    message = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"appId: {app_id}\nTest scenario in plain language: {scenario}",
            }
        ],
    )
    usage = Usage(message.usage.input_tokens, message.usage.output_tokens)

    if message.stop_reason == "refusal":
        raise GenerationError("the model declined this scenario")
    if message.stop_reason == "max_tokens":
        raise GenerationError(f"the flow was cut off at {MAX_TOKENS} output tokens")

    text = "".join(block.text for block in message.content if block.type == "text")
    flow_yaml = strip_fences(text)
    validate_flow(flow_yaml, app_id)
    return flow_yaml, usage


@dataclass
class LogEntry:
    timestamp: str
    model: str
    app_id: str
    scenario: str
    output: str
    generated_copy: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None


def record(output: Path, flow_yaml: str, model: str, app_id: str, scenario: str, usage: Usage,
           generated_dir: Path | None = None, log_file: Path | None = None) -> LogEntry:
    """Write the flow, an untouched copy for later diffing, and a log line."""
    generated_dir = generated_dir or GENERATED_DIR
    log_file = log_file or LOG_FILE
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(flow_yaml + "\n", encoding="utf-8")

    generated_dir.mkdir(parents=True, exist_ok=True)
    copy = generated_dir / output.name
    copy.write_text(flow_yaml + "\n", encoding="utf-8")

    entry = LogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        model=model,
        app_id=app_id,
        scenario=scenario,
        output=str(output),
        generated_copy=str(copy),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost_usd=usage.cost_usd(model),
    )
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry)) + "\n")
    return entry


def main(argv: list[str] | None = None, client=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app-id", required=True, help="mobile app id, or URL for web")
    parser.add_argument("--scenario", required=True, help="plain-language description of the scenario")
    parser.add_argument("--output", required=True, type=Path, help="path of the .yaml file to write")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model id (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="SDK retries for rate limits, overload and network errors (default: 3)")
    args = parser.parse_args(argv)

    import anthropic

    if client is None:
        # The SDK retries 408/409/429/5xx and connection errors with backoff.
        client = anthropic.Anthropic(max_retries=args.max_retries)

    try:
        flow_yaml, usage = generate_flow(client, args.app_id, args.scenario, args.model)
    except GenerationError as exc:
        print(f"ERROR: unusable flow: {exc}", file=sys.stderr)
        return 2
    except anthropic.AuthenticationError:
        print("ERROR: authentication failed; set ANTHROPIC_API_KEY or run `ant auth login`.", file=sys.stderr)
        return 1
    except anthropic.NotFoundError:
        print(f"ERROR: model {args.model!r} not found.", file=sys.stderr)
        return 1
    except anthropic.RateLimitError:
        print(f"ERROR: still rate limited after {args.max_retries} retries.", file=sys.stderr)
        return 1
    except anthropic.APIStatusError as exc:
        print(f"ERROR: API returned {exc.status_code}: {exc.message}", file=sys.stderr)
        return 1
    except anthropic.APIConnectionError:
        print("ERROR: could not reach the Anthropic API.", file=sys.stderr)
        return 1

    entry = record(args.output, flow_yaml, args.model, args.app_id, args.scenario, usage)

    print("--- Generated flow (review before committing!) ---")
    print(flow_yaml)
    print("---------------------------------------------------")
    cost = f"${entry.cost_usd:.4f}" if entry.cost_usd is not None else "unknown (model not in price table)"
    print(f"Tokens: {usage.input_tokens} in / {usage.output_tokens} out · cost {cost}")
    print(f"Flow written to: {args.output}")
    print(f"Untouched copy: {entry.generated_copy} (used by measure_edits.py)")
    print("Reminder: run `maestro test <file>` locally before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
