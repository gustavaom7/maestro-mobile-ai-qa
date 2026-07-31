#!/usr/bin/env python3
"""
CI Data Collector

Parses a Maestro JUnit report and appends the real run data to reports/test-runs.json.
Designed to be called from GitHub Actions workflow, after `maestro test --format junit`.

Usage:
  python scripts/collect_ci_data.py --junit-report results/mobile-report.xml
"""

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def parse_junit_report(report_path):
    """Parse a Maestro JUnit XML report into (status, duration, flows)."""
    tree = ET.parse(report_path)
    root = tree.getroot()
    testsuite = root.find("testsuite")
    if testsuite is None:
        raise ValueError(f"No <testsuite> found in {report_path}")

    flows = []
    for testcase in testsuite.findall("testcase"):
        testcase_status = testcase.get("status", "").upper()
        flows.append({
            "name": testcase.get("name"),
            "status": "passed" if testcase_status == "SUCCESS" else "failed",
            "duration": round(float(testcase.get("time", 0))),
            "retries": 0,
        })

    if not flows:
        raise ValueError(f"No flows found in {report_path}")

    duration = round(float(testsuite.get("time", 0)))
    status = "failed" if any(f["status"] == "failed" for f in flows) else "passed"

    return status, duration, flows


def collect_run_data(status, duration, flows):
    """Create run data object."""
    # Flake rate: Maestro's JUnit report doesn't expose per-flow retry counts,
    # so this stays 0 until Maestro surfaces that data.
    retry_count = sum(f.get("retries", 0) for f in flows)
    flake_rate = (retry_count / len(flows) * 100) if flows else 0

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
        "status": status,
        "duration": duration,
        "flake_rate": round(flake_rate, 2),
        "flows": flows,
    }


def append_to_file(run_data):
    """Append run data to test-runs.json."""
    runs_file = Path("reports/test-runs.json")

    # Load existing data
    if runs_file.exists():
        with open(runs_file) as f:
            runs = json.load(f)
    else:
        runs = []

    # Append new run
    runs.append(run_data)

    # Keep only last 90 runs (3 months if daily)
    runs = runs[-90:]

    # Save updated data
    runs_file.parent.mkdir(parents=True, exist_ok=True)
    with open(runs_file, "w") as f:
        json.dump(runs, f, indent=2)

    print(f"✅ Appended run data to {runs_file}")
    print(f"   Status: {run_data['status']}")
    print(f"   Duration: {run_data['duration']}s")
    print(f"   Flows: {len(run_data['flows'])}")
    print(f"   Flake rate: {run_data['flake_rate']}%")


def main():
    parser = argparse.ArgumentParser(description="Collect CI test run data from a Maestro JUnit report")
    parser.add_argument("--junit-report", required=True,
                        help="Path to the JUnit XML report produced by `maestro test --format junit`")

    args = parser.parse_args()

    status, duration, flows = parse_junit_report(args.junit_report)
    run_data = collect_run_data(status, duration, flows)
    append_to_file(run_data)


if __name__ == "__main__":
    main()
