"""
Generate a Maestro flow (YAML) from a plain-language scenario, using the
Anthropic API.

Goal: speed up writing test cases with an LLM without turning it into a black
box. The script always prints the generated flow for human review, because an
AI-generated test still needs review by someone who knows the app.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    python generate_flow.py \
        --app-id org.wikipedia \
        --scenario "Open the app, search for 'Test automation' and check that the first result shows" \
        --output ../../maestro/mobile/flows/04_generated_search.yaml
"""

import argparse
import os
import sys

import anthropic

SYSTEM_PROMPT = """You are a QA engineer who specializes in Maestro
(https://maestro.mobile.dev). Output ONLY a valid Maestro YAML flow, with no
explanation, no markdown and no backticks. The YAML must start with the
header "appId: <app_id>", then "---", then the list of commands. Use only
official Maestro commands (launchApp, tapOn, inputText, assertVisible,
takeScreenshot, back, scroll, swipe, etc). Prefer selectors by id or visible
text over fixed coordinates, and add a short comment above each logical block
of the test explaining its intent."""


def generate_flow(app_id: str, scenario: str) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"appId: {app_id}\n"
                    f"Test scenario in plain language: {scenario}"
                ),
            }
        ],
    )

    return "".join(
        block.text for block in message.content if block.type == "text"
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-id", required=True, help="mobile app id, or URL for web")
    parser.add_argument("--scenario", required=True, help="plain-language description of the scenario")
    parser.add_argument("--output", required=True, help="path of the .yaml file to write")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: set the ANTHROPIC_API_KEY environment variable.", file=sys.stderr)
        return 1

    flow_yaml = generate_flow(args.app_id, args.scenario)

    print("--- Generated flow (review before committing!) ---")
    print(flow_yaml)
    print("------------------------------------------------")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(flow_yaml + "\n")

    print(f"\nFlow written to: {args.output}")
    print("Reminder: run `maestro test <file>` locally before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
