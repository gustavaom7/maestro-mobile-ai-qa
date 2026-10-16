import measure_edits as me

GENERATED = """appId: org.wikipedia
---
# comment the model wrote
- launchApp
- tapOn: "Search"
- inputText: "Maestro"
- assertVisible: "Maestro"
"""

FINAL = """appId: org.wikipedia
---
- launchApp
- runFlow: ../subflows/skip_onboarding.yaml

- tapOn: "Search"
- inputText: "Maestro"
- assertVisible: "Title of respect given to a master musician"
"""


def test_ignores_comments_and_blank_lines():
    assert me.meaningful_lines("# x\n\n- launchApp   \n  # y\n") == ["- launchApp"]


def test_counts_kept_added_and_removed_lines():
    stats = me.compare("f.yaml", GENERATED, FINAL)
    assert (stats.generated, stats.final) == (6, 7)
    assert stats.kept == 5
    assert stats.added == 2
    assert stats.removed == 1
    assert round(stats.kept_ratio, 2) == 0.71


def test_untouched_flow_is_fully_kept():
    stats = me.compare("f.yaml", GENERATED, GENERATED)
    assert stats.added == stats.removed == 0
    assert stats.kept_ratio == 1.0


def test_main_reports_pairs_and_skips_missing(tmp_path, capsys):
    generated, flows = tmp_path / "generated", tmp_path / "flows"
    generated.mkdir()
    flows.mkdir()
    (generated / "a.yaml").write_text(GENERATED)
    (flows / "a.yaml").write_text(FINAL)
    (generated / "b.yaml").write_text(GENERATED)

    code = me.main(["--flows", str(flows), "--generated", str(generated), "--markdown"])

    out, err = capsys.readouterr()
    assert code == 0
    assert "| a.yaml | 6 | 7 | 5 | 2 | 1 | 71% |" in out
    assert "| TOTAL |" in out
    assert "skipped b.yaml" in err


def test_main_fails_without_pairs(tmp_path):
    (tmp_path / "g").mkdir()
    (tmp_path / "f").mkdir()
    assert me.main(["--flows", str(tmp_path / "f"), "--generated", str(tmp_path / "g")]) == 1
