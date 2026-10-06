#!/usr/bin/env bash
# Runs only after a failed test run: walks the app through the probe flows and prints what is
# actually on screen at each stop, so a failing selector can be fixed from the CI log alone.
set -u
for probe in .github/maestro-probes/*.yaml; do
  echo "=================== probe: $probe"
  maestro test "$probe" >/tmp/probe.log 2>&1 || { echo "(a probe step failed; the dump below is where it stopped)"; tail -5 /tmp/probe.log; }
  if maestro hierarchy >/tmp/hierarchy.json 2>/dev/null; then
    python3 scripts/ci_print_hierarchy.py /tmp/hierarchy.json
  else
    echo "(maestro hierarchy failed)"
  fi
done
echo "=================== Maestro debug output files"
find "$HOME/.maestro/tests" -maxdepth 2 -type f 2>/dev/null | sed "s|$HOME/||" | head -40
