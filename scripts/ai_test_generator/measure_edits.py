"""
Measure how much each AI-generated flow was edited before it passed.

generate_flow.py keeps an untouched copy of every flow in generated/. After
you fix a flow until `maestro test` passes, this script diffs the copy against
the committed flow and reports, per flow, the lines kept, changed, added and
removed, plus the share of the final flow that came from the model unchanged.

Usage:
    python measure_edits.py --flows ../../maestro/mobile/flows
    python measure_edits.py --flows ../../maestro/mobile/flows --markdown >> report.md
"""

from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATED_DIR = HERE / "generated"


def meaningful_lines(text: str) -> list[str]:
    """Lines that matter for a flow: no blank lines, no comments, no trailing spaces."""
    lines = []
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        lines.append(stripped)
    return lines


@dataclass
class EditStats:
    name: str
    generated: int
    final: int
    kept: int
    added: int
    removed: int

    @property
    def kept_ratio(self) -> float:
        """Share of the final flow's lines the model wrote unchanged."""
        return self.kept / self.final if self.final else 0.0


def compare(name: str, generated_text: str, final_text: str) -> EditStats:
    generated = meaningful_lines(generated_text)
    final = meaningful_lines(final_text)
    matcher = difflib.SequenceMatcher(a=generated, b=final, autojunk=False)
    kept = sum(block.size for block in matcher.get_matching_blocks())
    return EditStats(
        name=name,
        generated=len(generated),
        final=len(final),
        kept=kept,
        added=len(final) - kept,
        removed=len(generated) - kept,
    )


def collect(generated_dir: Path, flows_dir: Path) -> tuple[list[EditStats], list[str]]:
    stats, missing = [], []
    for copy in sorted(generated_dir.glob("*.yaml")):
        final = flows_dir / copy.name
        if not final.exists():
            missing.append(copy.name)
            continue
        stats.append(compare(copy.name, copy.read_text(encoding="utf-8"), final.read_text(encoding="utf-8")))
    return stats, missing


def render(stats: list[EditStats], markdown: bool) -> str:
    header = ["flow", "generated", "final", "kept", "added", "removed", "kept %"]
    rows = [[s.name, s.generated, s.final, s.kept, s.added, s.removed, f"{s.kept_ratio:.0%}"] for s in stats]
    if stats:
        kept = sum(s.kept for s in stats)
        final = sum(s.final for s in stats)
        rows.append(["TOTAL", sum(s.generated for s in stats), final, kept,
                     sum(s.added for s in stats), sum(s.removed for s in stats),
                     f"{kept / final:.0%}" if final else "0%"])
    if markdown:
        lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
        return "\n".join(lines)
    widths = [max(len(str(r[i])) for r in [header, *rows]) for i in range(len(header))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    return "\n".join(fmt.format(*map(str, r)) for r in [header, *rows])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--flows", required=True, type=Path, help="directory with the committed flows")
    parser.add_argument("--generated", type=Path, default=GENERATED_DIR, help="directory with the untouched copies")
    parser.add_argument("--markdown", action="store_true", help="print a Markdown table")
    args = parser.parse_args(argv)

    stats, missing = collect(args.generated, args.flows)
    if not stats:
        print(f"No generated flow in {args.generated} has a committed counterpart in {args.flows}.", file=sys.stderr)
        return 1
    print(render(stats, args.markdown))
    for name in missing:
        print(f"skipped {name}: not found in {args.flows}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
