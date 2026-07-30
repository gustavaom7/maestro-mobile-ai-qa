#!/usr/bin/env python3
"""
CI Data Collector

Collects test run data from a CI run and appends to reports/test-runs.json.
Designed to be called from GitHub Actions workflow.

Usage:
  python scripts/collect_ci_data.py \
    --status passed \
    --duration 145 \
    --flows "01_launch_app:passed:45,02_search_flow:passed:52,03_navigation_regression:passed:48"
"""

import json
import argparse
from datetime import datetime
from pathlib import Path


def parse_flows(flows_str):
    """Parse flows string into list of flow dicts.

    Format: "flow_name:status:duration,flow_name:status:duration"
    """
    if not flows_str:
        return []

    flows = []
    for flow_data in flows_str.split(","):
        parts = flow_data.strip().split(":")
        if len(parts) >= 3:
            flows.append({
                "name": parts[0],
                "status": parts[1],
                "duration": int(parts[2]),
                "retries": int(parts[3]) if len(parts) > 3 else 0,
            })
    return flows


def collect_run_data(status, duration, flows_str):
    """Create run data object."""
    flows = parse_flows(flows_str)

    if not flows:
        raise ValueError("No flows provided")

    # Calculate flake rate
    retry_count = sum(f.get("retries", 0) for f in flows)
    flake_rate = (retry_count / len(flows) * 100) if flows else 0

    run_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
        "status": status,
        "duration": duration,
        "flake_rate": round(flake_rate, 2),
        "flows": flows,
    }

    return run_data


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
    parser = argparse.ArgumentParser(description="Collect CI test run data")
    parser.add_argument("--status", required=True, choices=["passed", "failed"],
                        help="Overall test status")
    parser.add_argument("--duration", required=True, type=int,
                        help="Total duration in seconds")
    parser.add_argument("--flows", required=True,
                        help="Comma-separated flows: flow_name:status:duration[:retries]")

    args = parser.parse_args()

    run_data = collect_run_data(args.status, args.duration, args.flows)
    append_to_file(run_data)


if __name__ == "__main__":
    main()
