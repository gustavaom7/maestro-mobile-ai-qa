# Architecture and place in the SDLC

## Day-to-day flow

1. A developer opens a pull request; `mobile-tests.yml` runs the mobile suite on an Android emulator.
2. Anyone can run the suite on demand from the Actions tab. There is no nightly schedule, to save Actions minutes; a team with a release cadence would add one.
3. A failure produces (a) a JUnit report artifact, (b) a Slack message with a direct link to the run, and (c) the on-screen texts of each failed step in the job log.
4. QA (or the developer) reviews the report and files a bug in Jira/Linear if it is a real regression.
5. New scenarios start from `ai_test_generator`, always reviewed by a person before the commit.

## Decisions and trade-offs

- **Maestro instead of plain Appium/Selenium:** declarative YAML that is quicker to maintain and easier to review than traditional automation code, so QA and developers can read each other's tests. (The [Appium repo](https://github.com/gustavaom7/appium-mobile-e2e-framework) covers what YAML flows cannot express.)
- **Emulator in CI instead of a physical device:** cheaper and reproducible; physical devices stay for performance and battery checks, which are outside this repo.
- **Web in beta:** documented as a known risk (`docs/web-fallback-playwright.md`), not hidden.
