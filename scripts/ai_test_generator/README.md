# AI-powered test generation

A small script that turns a plain-language test scenario into a Maestro `.yaml` flow, using the Anthropic API (Claude).

## Why

It speeds up the first draft of a flow. It does not generate whole suites on its own: a QA engineer still reviews the draft, fixes selectors and runs it locally before committing.

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
python generate_flow.py \
  --app-id org.wikipedia \
  --scenario "Open the app, go to settings, toggle dark mode, then confirm the screen turned dark" \
  --output ../../maestro/mobile/flows/11_dark_mode_toggle.yaml
```

## Next step: LLM-suggested selector fixes

When a flow fails because a selector broke (for example, a button's text changed), send the old YAML and the current UI tree (`maestro hierarchy`) to the LLM, ask for a corrected selector, and open a pull request for a person to review instead of only reporting the failure to Slack.
