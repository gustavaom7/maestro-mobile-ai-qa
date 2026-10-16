"""Print the visible texts and ids of a `maestro hierarchy` JSON dump, one element per line."""
import json
import sys

seen = []


def walk(node):
    if isinstance(node, dict):
        attrs = node.get("attributes") or {}
        parts = [f"{k}={attrs[k]!r}" for k in ("text", "accessibilityText", "hintText", "resource-id") if attrs.get(k)]
        if parts:
            line = "  ".join(parts)
            if line not in seen:
                seen.append(line)
        for child in node.get("children") or []:
            walk(child)


walk(json.load(open(sys.argv[1])))
print("\n".join(seen[:150]) if seen else "(empty hierarchy)")
