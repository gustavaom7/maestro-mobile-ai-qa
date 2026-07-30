# QA Automation Portfolio — Maestro + CI/CD + AI-Assisted Testing

A portfolio repository demonstrating an **AI-first** QA automation stack: mobile and web testing with [Maestro](https://maestro.mobile.dev), daily CI/CD pipeline on GitHub Actions with automated Slack reporting, and an AI-powered utility to accelerate test case generation.

> This project is built as a learning/portfolio artifact, not production software. Where features are still experimental (e.g., Maestro web support), that's explicitly flagged — I prefer transparency about real tool state over simulating what doesn't work.

## Why this project exists

Built to address a **QA Automation Engineer** job description asking for:

| Job Requirement | Where in this repo | Status |
|---|---|---|
| Manual, functional, regression, and exploratory tests | `docs/manual-test-cases.md` | ✅ |
| Automated mobile and web test suites | `maestro/mobile`, `maestro/web` | ✅ Mobile (3/3 passing) / ⚠️ Web (beta) |
| CI/CD integration (GitHub Actions) running daily | `.github/workflows/` | ✅ |
| Automated Slack reporting | `notifications/slack_notify.sh` | ✅ Configured |
| LLM-assisted intelligent test generation | `scripts/ai_test_generator/` | ✅ Tested |
| SDLC / Agile / defect lifecycle | `docs/architecture.md` | ✅ |

## Architecture

```mermaid
flowchart LR
    A[Daily GitHub Actions cron] --> B[Job Mobile: Android emulator + Maestro]
    A --> C[Job Web: Headless browser + Maestro Web]
    B --> D[JUnit/HTML report]
    C --> D
    D --> E[slack_notify.sh]
    E --> F((Slack channel))
    G[Natural language description] --> H[ai_test_generator]
    H --> I[New Maestro flow .yaml]
    I --> B
    I --> C
```

## Project structure

```
maestro/
  mobile/flows/     -> Android Wikipedia app flows (open source, public)
  web/flows/        -> the-internet.herokuapp.com flows (QA practice site)
scripts/
  ai_test_generator/ -> Generates Maestro flows from text descriptions (Anthropic API)
notifications/
  slack_notify.sh    -> Posts run summary to Slack via webhook
.github/workflows/
  mobile-tests.yml   -> Runs Android emulator + Maestro, daily and on PRs
  web-tests.yml      -> Runs Maestro web tests, daily and on PRs
docs/
  architecture.md
  manual-test-cases.md
```

## App under test (mobile)

**Wikipedia for Android** (`org.wikipedia`): open source, publicly available. It's also used in official Maestro tutorials, making it easy for anyone to reproduce tests without credentials or private apps.

## Scope: Android + Web (iOS intentionally excluded)

Maestro supports iOS identically to Android (same flow syntax). I deliberately excluded iOS from this portfolio due to time prioritization: setting up iOS (Xcode + simulator) wouldn't add relevant learning beyond what Android demonstrates. That time was invested in CI/CD depth, automated reporting, and AI-assisted test generation — the kind of trade-offs QA engineers make under real deadlines.

## App under test (web)

`https://the-internet.herokuapp.com` — a classic QA practice site with intentionally difficult elements (drag-and-drop, iframes, dynamic content), good for demonstrating depth beyond happy paths.

## Running locally

### Mobile and web tests

```bash
# Install Maestro
curl -Ls "https://get.maestro.mobile.dev" | bash

# Run mobile tests
maestro test maestro/mobile/flows/

# Run web tests (requires Chrome/browser)
maestro test maestro/web/flows/
```

### AI-powered test generator

```bash
# Setup
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Generate a new test flow from natural language description
python scripts/ai_test_generator/generate_flow.py \
  --app-id org.wikipedia \
  --scenario "Open app, navigate to settings, toggle dark mode" \
  --output maestro/mobile/flows/05_dark_mode.yaml

# Review the generated flow, run locally, then commit
maestro test maestro/mobile/flows/05_dark_mode.yaml
git add maestro/mobile/flows/05_dark_mode.yaml
git commit -m "Add dark mode toggle test (AI-generated)"
```

## CI/CD Status

- **Mobile Tests**: ✅ Passing (3 flows: launch_app, search_flow, navigation_regression)
- **Web Tests**: ⚠️ Beta (Maestro web support is experimental; see `docs/web-fallback-playwright.md`)
- **Slack Notifications**: ✅ Active
- **Schedule**: Daily at 9 AM UTC + on every pull request

## Design decisions and trade-offs

### Android-only (iOS not included)

iOS exclusion was a deliberate prioritization decision. Maestro supports iOS with identical syntax, but setting up the environment (Xcode + simulator) wouldn't add relevant technical learning beyond Android. Time was prioritized for CI/CD depth, automated notifications, and AI-assisted generation — real trade-offs QA engineers make constantly.

### Web: Maestro beta support vs Playwright

Maestro web support is still beta. Web flows use current syntax (`url:`) but may need adjustments if Maestro versions diverge. A Playwright fallback is documented in `docs/web-fallback-playwright.md`. This exemplifies a real QA trade-off: adopt newer tools with more uncertainty, or stick with mature solutions.

## Next steps (if evolving further)

- Real auto-healing: send broken selector + current UI tree to LLM for corrected selectors
- Predictive failure detection: use failure history per flow to prioritize execution
- Simple static HTML dashboard consolidating both job results
- Jira/Linear integration to auto-create tickets for recurring failures
