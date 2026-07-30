# Test Analytics Dashboard

A comprehensive, interactive HTML dashboard for monitoring test suite health and performance over time.

## Overview

The dashboard provides real-time insights into:
- **Pass Rate Trends** — How many tests pass/fail over time
- **Execution Time Trends** — Performance regression detection
- **Per-Flow Health** — Which flows are most flaky
- **Retry Analysis** — How often tests need retries (indicator of flakiness)

## Features

### Metric Cards (Top)
```
┌─────────────────────────────────────┐
│ Pass Rate: 100.0%  │  Flake Rate: 0.0%  │  Avg Duration: 146.7s  │
│ 11 total runs      │  Runs with retries │  Per full suite run    │
└─────────────────────────────────────┘
```

### Interactive Charts

**1. Pass Rate Trend (Last 30 Runs)**
- Line chart showing pass percentage over time
- Hover to see exact values per run
- Helps detect gradual quality degradation

**2. Execution Time Trend**
- Track suite performance over time
- Alert if execution time increases >20% (potential regression)

**3. Pass Rate by Flow**
- Horizontal bar chart
- Quickly identify which flows are most flaky
- Color-coded: green (>98%), yellow/red (<98%)

**4. Retry Count by Flow**
- How many times each flow had to retry
- Flaky flows show high retry counts

**5. Per-Flow Health Table**
- Detailed stats for each flow
- Pass rate, total runs, failures, avg duration, retries
- Sortable columns

## How It's Generated

### Automatic (CI/CD)

Every mobile test run triggers:

1. **Collect Data** (`scripts/collect_ci_data.py`)
   - Parses test results from CI run
   - Extracts: pass/fail status, duration, retries
   - Appends to `reports/test-runs.json`

2. **Generate Dashboard** (`scripts/generate_dashboard.py`)
   - Reads `reports/test-runs.json`
   - Calculates metrics and trends
   - Renders HTML with Chart.js visualizations

3. **Upload Artifact** (GitHub Actions)
   - Dashboard saved as artifact
   - Accessible from workflow run page
   - Retained for 90 days

### Manual Local Generation

```bash
# 1. Ensure test data exists
ls reports/test-runs.json

# 2. Generate dashboard
python3 scripts/generate_dashboard.py

# 3. Open in browser
open reports/test-dashboard.html
```

## Data Format (test-runs.json)

```json
[
  {
    "timestamp": "2026-07-30",
    "status": "passed",
    "duration": 145,
    "flake_rate": 0.0,
    "flows": [
      {
        "name": "01_launch_app",
        "status": "passed",
        "duration": 45,
        "retries": 0
      },
      {
        "name": "02_search_flow",
        "status": "passed",
        "duration": 52,
        "retries": 0
      },
      {
        "name": "03_navigation_regression",
        "status": "passed",
        "duration": 48,
        "retries": 0
      }
    ]
  }
  // ... more runs
]
```

### Adding Manual Run Data

You can manually add test data from local runs:

```bash
python3 scripts/collect_ci_data.py \
  --status passed \
  --duration 145 \
  --flows "01_launch_app:passed:45,02_search_flow:passed:52,03_navigation_regression:passed:48"
```

**Format:**
- `--status`: `passed` or `failed`
- `--duration`: total seconds
- `--flows`: comma-separated `name:status:duration[:retries]`

## Interpreting the Dashboard

### Healthy Signals ✅

- **Pass Rate:** 99%+ (100% is realistic target)
- **Flake Rate:** <1% (occasional retry due to external factors)
- **Execution Time:** Consistent ±5% day-to-day
- **All Flows Green:** All flows >95% pass rate

### Warning Signals 🟡

- **Pass Rate Trend:** Declining over last 5 runs → investigate commits
- **Flake Rate:** >5% → some flows are unstable → review retries
- **Execution Time:** Increasing >20% → potential regression or device slowdown

### Critical Signals 🔴

- **Pass Rate:** <90% → blocking issue, halt releases
- **Any Flow Red:** <50% pass rate → critical instability
- **Execution Time:** 2-3x baseline → severe performance regression

## Maintenance

### Retention Policy

- **Data:** Last 90 runs kept (3 months if daily schedule)
- **Artifacts:** Deleted after 90 days (GitHub Actions default)
- **Local:** No automatic cleanup

### Troubleshooting

**Dashboard shows no data:**
```bash
# Check if test-runs.json exists and has content
cat reports/test-runs.json | jq .

# If empty, manually add sample data:
python3 scripts/collect_ci_data.py \
  --status passed \
  --duration 145 \
  --flows "01_launch_app:passed:45,02_search_flow:passed:52,03_navigation_regression:passed:48"
```

**Charts not rendering:**
- Clear browser cache (Ctrl+Shift+Delete)
- Check browser console for JavaScript errors
- Ensure Chart.js CDN is accessible (requires internet)

**Dashboard outdated:**
- Regenerate locally: `python3 scripts/generate_dashboard.py`
- Or download latest from GitHub Actions artifact

## Integration Examples

### Adding to CI Email Report
```bash
# After generating dashboard
echo "Dashboard: reports/test-dashboard.html" >> email_body.txt
```

### GitHub Pages Deployment
```bash
# Add to CI workflow to deploy dashboard to gh-pages branch
- name: Deploy dashboard to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./reports
    destination_dir: dashboard
```

### Slack Notification with Link
```bash
# Extend slack_notify.sh to include dashboard artifact link
DASHBOARD_URL="https://github.com/$REPO/actions/runs/$RUN_ID/artifacts"
curl -X POST "$SLACK_WEBHOOK_URL" -H 'Content-Type: application/json' \
  -d "{\"text\": \"Dashboard: $DASHBOARD_URL\"}"
```

## Future Enhancements

- **Real-time updates:** WebSocket connection to CI for live dashboard
- **Anomaly detection:** ML model to detect unusual flake patterns
- **Device matrix:** Show results by device (Galaxy A15, emulator, etc.)
- **Comparison view:** Compare two date ranges
- **Regression detection:** Alert when new flow failures appear
- **Performance analytics:** Response time by interaction (tap, scroll, input)

## Files

| File | Purpose |
|---|---|
| `scripts/generate_dashboard.py` | Main dashboard generator |
| `scripts/collect_ci_data.py` | CI data collector (for workflow) |
| `reports/test-runs.json` | Raw test run data (JSON) |
| `reports/test-dashboard.html` | Generated dashboard (HTML) |
| `.github/workflows/mobile-tests.yml` | CI workflow with dashboard generation |

---

**Note:** Dashboard is generated automatically after each CI run. For manual testing, run `python3 scripts/generate_dashboard.py` locally after `maestro test`.
