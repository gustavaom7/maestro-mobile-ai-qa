# Testing Strategy

## Scope

**App under test:** Wikipedia for Android (`org.wikipedia`), F-Droid build 50598, pinned so a new release cannot silently change what the flows assert on.

| Flow | Type | What it checks |
|---|---|---|
| `01_launch_app` | Smoke | Launch on a clean state, onboarding, Home feed |
| `02_search_flow` | Functional | Search, open a result, article content |
| `03_navigation_regression` | Regression | Bottom-tab navigation |
| `04_save_article` | Functional | Save an article, find it in the Saved list by title |
| `05_remove_saved_article` | Functional | Remove a saved article, list updates |
| `06_change_language` | Functional | Switch an article to Português and back to English |
| `07_search_no_results` | Negative | A query with no results shows the empty state |
| `08_change_theme` | Functional | Switch the article theme to Dark and back |
| `09_change_text_size` | Functional | Increase article text size and revert |
| `10_share_article` | Integration | Share sheet opens with the article URL |

Not covered: sign-in, offline mode, iOS (Maestro supports it with the same syntax; left out to keep CI on one free Linux runner). Web flows exist but are disabled while Maestro's web support is in beta (`docs/web-fallback-playwright.md`).

## Resilience patterns

- **Clean state per flow.** Every flow starts with `launchApp: clearState: true`, so no flow depends on what the previous one left behind.
- **Pop-ups closed by id, in shared subflows.** Onboarding, the search-widget promo, the "Wikipedia games" dialog and the donate modal each have a subflow in `maestro/mobile/subflows/` that closes them by their button id, with `optional: true` because they don't always appear. Coordinate taps are not used: when the pop-up was absent, they landed on the app's own UI.
- **Wait on the UI, not on the clock.** `waitForAnimationToEnd` and assertions on the next screen instead of fixed sleeps.
- **Bounded loops instead of fixed counts.** `back_to_tabs` presses back until the tab bar is visible, at most 5 times; onboarding takes the exit each screen offers, at most 8 passes.

This is defensive flow design, not self-healing: when the app renames a selector, the flow fails and a person fixes it.

## CI failures and their root causes

When the flows were first run in CI, 7 of 10 failed. Each fix below came from evidence (probe flows that dump the on-screen texts and ids on failure), not from adding retries.

| Symptom | Root cause | Fix |
|---|---|---|
| Results moved between 7/10 and 10/10 failing | Six blind taps at the bottom-right corner to skip onboarding ran past the carousel, hit More → Donate and left a Chrome tab open in the app's task | Clean state per flow; skip onboarding by its buttons |
| Every flow blocked behind a system dialog | "Pixel Launcher isn't responding" ANR on the CI emulator | `hide_error_dialogs` on the emulator; tap "Wait" if it still shows |
| Stuck on the first onboarding screen | This app build has a Forward arrow and no Skip on screen 1 | Shared `skip_onboarding` subflow taking whichever exit each screen offers |
| Nine flows stopped right after tapping Search | "A Faster way to Search" bottom sheet over the search box | `dismiss_search_widget_promo` subflow |
| Six flows failed right after opening an article | "Introducing Wikipedia games" dialog over the toolbar | `dismiss_article_popups` subflow |
| Saved tab never found | Two fixed backs no longer reached the tab bar | `back_to_tabs` subflow, Saved opened by id |
| Share assertion failed | This Android version's share sheet previews only the link | Assert the article URL |
| "Português" never found | The language list is alphabetical and only its first entries fit on screen | Scroll to it, and to "English" on the way back |

After these fixes all 10 flows pass in CI: about 21 minutes of flows, 24 minutes for the whole job. That is one green run, not a flake rate; a rate needs a run history this repo does not have yet, since CI runs only on pull requests and on demand.

## CI environment

| Property | Value |
|---|---|
| Runner | `ubuntu-latest` with KVM |
| Emulator | API 33, Google APIs, x86_64, Pixel 6 profile |
| Trigger | Every pull request and manual runs (no schedule, to save Actions minutes) |
| Reports | JUnit XML, an HTML dashboard artifact, Slack message when `SLACK_WEBHOOK_URL` is set |
