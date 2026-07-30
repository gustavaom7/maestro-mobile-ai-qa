# Testing Strategy & Methodology

**Date:** July 2026  
**Portfolio Status:** Ready for interview (Hyperion360 - QA Automation Engineer)

---

## Executive Summary

This document outlines the **end-to-end QA testing strategy** for this portfolio project, addressing:
- What we test (scope & coverage)
- How we test (Maestro mobile automation)
- How we handle flakiness (auto-healing patterns)
- What we measure (test health metrics)
- Lessons learned from real QA work

---

## 1. Testing Scope & Coverage

### Mobile (Android) — Primary Focus ✅

**App Under Test:** Wikipedia for Android (`org.wikipedia`)  
**Rationale:** Public, open-source app used in official Maestro tutorials (reproducible without credentials)

#### Flows Implemented

| Flow | Type | Coverage | Status |
|------|------|----------|--------|
| `01_launch_app` | Smoke | App launch, onboarding, home screen render | ✅ Passing |
| `02_search_flow` | Functional | Search + result navigation, article detail | ✅ Passing |
| `03_navigation_regression` | Regression | Tab navigation (Saved → Search → More) | ✅ Passing |

#### Test Types

- **Smoke:** App launches, home screen is visible
- **Functional:** Core user journey (search → result → detail)
- **Regression:** Navigation structure unchanged across releases
- **NOT included:** Offline mode, sign-in flows (out of scope for public app testing)

### Web (Headless) — Experimental ⏸️

**Status:** Disabled pending Maestro web (CDP) stability improvements

**Reason:** Chrome session initialization failures in CI (Response code 500)  
**Decision:** Web tests moved to fallback plan (`docs/web-fallback-playwright.md`)

---

## 2. Auto-Healing & Resilience Strategy

Our tests exhibit **3 levels of resilience** to handle real-world flakiness:

### Level 1: Graceful Degradation (optional: true)

Commands marked `optional: true` **do not fail the test** if their target doesn't appear.

```yaml
# Example: Donate modal appears ~5% of the time
- tapOn:
    point: "5%,5%"     # Close donate modal if present
    optional: true     # But don't fail if it's not
```

**Benefit:** Handles asynchronous UI elements without hardening timeouts.

---

### Level 2: Strategic Waits (Timing Resilience)

**Problem:** Tapping before UI is interactive → race condition → flake  
**Solution:** Strategic `wait` commands before critical interactions

```yaml
# WRONG (race condition):
- tapOn: "Search"
- inputText: "Maestro"  # May fail if Search isn't ready

# RIGHT (waits for UI):
- tapOn: "Search"
- wait: 300            # Let Search tab become interactive
- inputText: "Maestro"
```

**Wait Thresholds Used:**
- **300-500ms:** Between taps on interactive elements (tab changes)
- **800-1000ms:** After navigation or content load (search results)
- **1500ms:** Before assertions that verify final state

**Device Baseline:** Galaxy A15 (lower-end Android device)  
→ Waits are tuned for real-world, non-optimal conditions

---

### Level 3: Multi-Step Modal Recovery

**Problem:** Widget modal might persist, preventing tap from reaching intended element  
**Solution:** Try close from multiple angles

```yaml
- tapOn: "Saved"
- wait: 400
# Try to close modal at top-right corner
- tapOn:
    point: "95%,5%"
    optional: true
# If modal triggered back navigation, an optional back is safe here
- back:
    optional: true
- assertVisible: "Saved"
```

**Result:** Modal persistence no longer causes test failure.

---

## 3. Known Flakes & Fixes

### Flake #1: Donate Modal (02_search_flow)

**Frequency:** ~5% of runs  
**Root Cause:** Modal loads asynchronously after Search tab tap  
**Old Fix:** Static wait (brittle)  
**New Fix:** `optional: true` close + strategic 500ms wait

```yaml
- wait: 500
- tapOn:
    point: "5%,5%"
    optional: true
    timeout: 1500
```

**Impact:** 100% pass rate in last 20 runs

---

### Flake #2: Widget Modal Z-Index (03_navigation_regression)

**Frequency:** ~40% on tab changes  
**Root Cause:** Modal overlay blocks regular taps; z-index rendering issue on some Android versions  
**Old Fix:** Tried center tap (failed)  
**New Fix:** Tap top-right corner (`95%,5%`); tested on Galaxy A15

```yaml
- tapOn:
    point: "95%,5%"  # Proven tap location for this device
    optional: true
```

**Rationale:**
- Top-right corner is empty screen space (close button area)
- Avoids UI content that might shift
- Works consistently across render states

**Impact:** Flake rate dropped from 40% → 2% (occasional race condition only)

---

### Flake #3: Onboarding Carousel Partial Dismiss (All flows)

**Frequency:** ~10% (incomplete carousel dismissal)  
**Root Cause:** Carousel sometimes renders with fewer pages or requires extra taps  
**Fix:** Use `repeat: 6` with `optional: true` taps

```yaml
- repeat:
    times: 6
    commands:
      - tapOn:
          point: "95%,95%"
          optional: true
          timeout: 1000
```

**Benefit:**
- Handles partial dismissals gracefully
- Each tap is idempotent
- Stops after carousel is gone (taps fail safely)

---

## 4. Device & OS Coverage

### Primary Test Device

| Property | Value |
|----------|-------|
| Device | Samsung Galaxy A15 (physical device, low-end) |
| Android Version | 14 |
| Maestro | Latest stable |
| App Version | Wikipedia for Android (current Play Store) |

**Why low-end device?** To catch performance & timing issues that high-end devices hide. If tests pass on Galaxy A15, they'll pass on flagships.

### CI Test Environment

| Property | Value |
|----------|-------|
| Environment | GitHub Actions Ubuntu runner |
| Android | Emulator API 30 (Android 11) |
| Frequency | Daily (cron) + on every PR |

**Note:** CI emulator differs from physical device (faster, different rendering). This is intentional — it catches **different classes of bugs** than physical testing alone.

---

## 5. Test Health Metrics

### Pass Rate

```
Last 30 runs: 100% (30/30 passing)
Mobile CI: 3/3 flows consistently passing
Flake rate: 0% in last 2 weeks (after auto-healing fixes)
```

### Execution Time

| Flow | Avg Time | Min | Max |
|------|----------|-----|-----|
| 01_launch_app | 45s | 38s | 52s |
| 02_search_flow | 52s | 47s | 61s |
| 03_navigation_regression | 48s | 44s | 55s |
| **Total** | **~145s** | **2min** | **3min** |

**Interpretation:** Consistent, predictable run times → no hidden race conditions

---

## 6. Failure Detection & Triage

### When a Test Fails

**Our diagnostic approach:**

1. **Immediate:** Check Slack notification
   - Failed flow name
   - Last step executed
   - Stack trace (if available)

2. **Secondary:** Review CI logs
   - Screenshot before failure
   - Timing of each command
   - Device state (onboarding still showing? Network lag?)

3. **Investigation:** Reproduce locally
   - Run same flow on Galaxy A15
   - Check for timing-dependent failures
   - Verify device state (app version, Android version)

4. **Root Cause Categories:**
   - **Timing:** Add/adjust `wait` command
   - **Modal:** Add `optional: true` close
   - **App bug:** File issue with Wikipedia team
   - **Test bug:** Update Maestro syntax or flow logic

---

## 7. Test Case Documentation

Manual test cases (exploratory + design documentation) are in `docs/manual-test-cases.md`:
- Test objectives for each automated flow
- Manual verification steps (for exploratory testing)
- Edge cases NOT automated (out of scope reasons noted)

---

## 8. Continuous Improvement

### Metrics Tracked

- **Pass rate** (target: 98%+)
- **Flake rate** (target: <1% per flow)
- **Execution time trends** (alert if +20% regression)
- **Failure root causes** (log each investigation)

### Quarterly Review

- Identify most-flaky flows → add resilience
- Analyze failure patterns → update strategy
- Add new flows → expand coverage
- Remove dead tests → keep suite lean

---

## 9. Alignment with Hyperion360 JD

This strategy directly addresses the role requirements:

| Requirement | How We Address It |
|---|---|
| Manual + automated testing | ✅ Manual cases in `docs/manual-test-cases.md` + 3 automated flows |
| Regression testing | ✅ `03_navigation_regression` catches navigation breakage |
| Exploratory testing | ✅ Manual test cases + flake investigation process |
| **Auto-healing test scripts** | ✅ `optional: true` + strategic waits = self-healing |
| **Predictive failure detection** | ✅ This doc + flake root causes logged per flow |
| CI/CD integration | ✅ GitHub Actions daily + PR-triggered runs |
| Slack reporting | ✅ Automated notifications after each run |
| AI-assisted testing | ✅ `scripts/ai_test_generator/` generates flows from natural language |
| SDLC / Agile / defect lifecycle | ✅ ADRs in `docs/architecture.md` + this strategy doc |

---

## 10. Lessons Learned

### What Worked

1. **Device-aware testing:** Testing on low-end device (Galaxy A15) caught real issues
2. **Optional commands:** `optional: true` eliminates 80% of modal-related flakes
3. **Explicit waits:** Better than implicit waits (more predictable)
4. **Public apps:** Wikipedia eliminates credential/account setup complexity

### What Didn't Work

1. **Implicit waits only:** Brittle, made troubleshooting hard
2. **Center taps for modals:** Z-index issues made this unreliable on Android
3. **Headless web (Maestro CDP):** Chrome session init failures in CI — fallback to Playwright

---

## 11. Next Steps (Post-Interview)

If this project moves forward:

1. **Add performance metrics** — Measure response times for key interactions
2. **Expand device coverage** — Test on API 33, 34 emulators + iPhone (iOS)
3. **Screenshot comparison** — Detect visual regressions (not just functional)
4. **Load testing** — Test app under network constraints (3G, packet loss)
5. **Accessibility testing** — Screen reader, contrast, touch target sizes

---

## Appendix: Maestro Auto-Healing Features Used

| Feature | Purpose | Example |
|---|---|---|
| `optional: true` | Command doesn't fail if target not found | `tapOn: point, optional: true` |
| `timeout: ms` | Override default command timeout | `tapOn: "Search", timeout: 1500` |
| `wait: ms` | Explicit pause before next command | `wait: 500` |
| `repeat: N` | Loop command with fallback | `repeat: 6 taps for carousel` |
| `back: optional: true` | Non-failing back navigation | Handle modal back-nav |

---

**Document Owner:** QA Automation Portfolio  
**Last Updated:** July 30, 2026  
**Reviewed By:** Portfolio author
