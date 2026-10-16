# Fallback: web tests without Maestro's beta web support

Maestro's web support is still evolving, and its configuration syntax (`url:` vs `webUrl:` vs a CLI flag) can change between versions. That is the real trade-off here: adopt a new feature and accept the risk, or use a mature tool.

If stability matters more, the same logical suite (`homepage_load`, `dropdown_and_dynamic_content`) can be rewritten in Playwright or Selenium without losing coverage, keeping Maestro for mobile only. Both run in the same CI jobs; only the execution step changes. The [Playwright repo](https://github.com/gustavaom7/playwright-typescript-e2e-framework) is that choice made for a full web suite.
