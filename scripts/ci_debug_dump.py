"""Print what was on screen when each Maestro flow failed, straight into the CI log.

Artifacts can't always be opened where the run is triaged, so this walks Maestro's debug
output (~/.maestro/tests) and prints, per failed command, the error and the visible texts
of the UI hierarchy Maestro recorded with it (when present).
"""
import json
import pathlib
import sys

root = pathlib.Path.home() / ".maestro" / "tests"
if not root.exists():
    print(f"no Maestro debug output at {root}")
    sys.exit(0)


def texts(node, out):
    if isinstance(node, dict):
        attrs = node.get("attributes", node)
        for key in ("text", "accessibilityText", "hintText", "resource-id"):
            value = attrs.get(key) if isinstance(attrs, dict) else None
            if value and isinstance(value, str) and value not in out:
                out.append(value)
        for value in node.values():
            texts(value, out)
    elif isinstance(node, list):
        for item in node:
            texts(item, out)
    return out


for commands_file in sorted(root.rglob("commands-*.json")):
    entries = json.loads(commands_file.read_text())
    failed = [e for e in entries if (e.get("metadata") or {}).get("status") == "FAILED"]
    print(f"\n=== {commands_file.name}: {len(entries)} commands, {len(failed)} failed")
    for entry in failed:
        meta = entry["metadata"]
        command = {k: v for k, v in entry.get("command", {}).items() if v}
        print("failed command:", json.dumps(command)[:300])
        error = meta.get("error") or {}
        print("error:", (error.get("message") if isinstance(error, dict) else str(error))[:300])
        seen = texts(error, []) if isinstance(error, dict) else []
        print("texts on screen:", seen[:80] if seen else "(no hierarchy recorded)")
    if not failed:
        steps = [list((e.get("command") or {}).keys())[:1] for e in entries]
        print("steps:", steps[:40])
