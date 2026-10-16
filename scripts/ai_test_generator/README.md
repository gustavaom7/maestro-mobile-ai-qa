# AI-powered test generation

A small tool that turns a plain-language test scenario into a Maestro `.yaml` flow, using the Anthropic API (Claude), and measures how much each generated flow had to be edited before it passed.

## Why

It speeds up the first draft of a flow. It does not generate whole suites on its own: a QA engineer still reviews the draft, fixes selectors and runs it locally before committing. The measurement step keeps that claim honest: instead of "AI writes our tests", the repo reports how much of each passing flow the model actually wrote.

## Setup

```bash
pip install -r requirements.txt        # anthropic, pyyaml
export ANTHROPIC_API_KEY=sk-ant-...    # or `ant auth login`
```

## Generate a flow

```bash
python generate_flow.py \
  --app-id org.wikipedia \
  --scenario "Open the app, go to settings, toggle dark mode, then confirm the screen turned dark" \
  --output ../../maestro/mobile/flows/11_dark_mode_toggle.yaml
```

What it does:

- Asks the model for a flow (default model `claude-sonnet-4-6`, change it with `--model`).
- Rejects an answer it cannot use, and writes nothing: not valid YAML, no `appId` header or the wrong one, an empty command list, a cut-off answer (`max_tokens`) or a refusal. A markdown fence the model adds anyway is removed.
- Lets the SDK retry rate limits, overload and network errors with backoff (`--max-retries`, default 3).
- Writes the flow, an untouched copy in `generated/`, and one line in `generations.jsonl` with the model, tokens and cost in USD.

## Measure the edits

Fix the flow until `maestro test` passes, commit it, then:

```bash
python measure_edits.py --flows ../../maestro/mobile/flows            # table
python measure_edits.py --flows ../../maestro/mobile/flows --markdown  # for the README
```

For each flow it diffs the untouched copy against the committed flow, ignoring comments and blank lines, and reports the lines kept, added and removed, and **kept %**: the share of the final flow the model wrote unchanged.

Commit `generated/` and `generations.jsonl` together with the fixed flows, so anyone can rerun the measurement.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

The tests use a fake client, so they need no API key and cost nothing. They run in CI on every change under this folder (`.github/workflows/python-tests.yml`).

## Next step: LLM-suggested selector fixes

When a flow fails because a selector broke (for example, a button's text changed), send the old YAML and the current UI tree (`maestro hierarchy`) to the LLM, ask for a corrected selector, and open a pull request for a person to review instead of only reporting the failure to Slack.
