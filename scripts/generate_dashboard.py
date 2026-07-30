#!/usr/bin/env python3
"""
Test Analytics Dashboard Generator

Generates an HTML dashboard with interactive charts showing:
- Pass rate trends over time
- Flake rate per flow
- Execution time trends
- Overall test health metrics

Reads from: reports/test-runs.json
Outputs to: reports/test-dashboard.html
"""

import json
import os
from datetime import datetime
from pathlib import Path


def load_test_runs():
    """Load test run data from JSON file."""
    runs_file = Path("reports/test-runs.json")
    if not runs_file.exists():
        return []

    with open(runs_file) as f:
        return json.load(f)


def calculate_metrics(runs):
    """Calculate overall test health metrics."""
    if not runs:
        return {
            "total_runs": 0,
            "pass_rate": 0,
            "avg_time": 0,
            "flake_rate": 0,
        }

    total_runs = len(runs)
    passed = sum(1 for r in runs if r.get("status") == "passed")
    pass_rate = (passed / total_runs * 100) if total_runs > 0 else 0

    avg_time = sum(r.get("duration", 0) for r in runs) / total_runs if total_runs > 0 else 0

    # Flake rate: runs that passed but had retries
    flaky_runs = sum(1 for r in runs if r.get("retries", 0) > 0)
    flake_rate = (flaky_runs / total_runs * 100) if total_runs > 0 else 0

    return {
        "total_runs": total_runs,
        "pass_rate": round(pass_rate, 1),
        "avg_time": round(avg_time, 1),
        "flake_rate": round(flake_rate, 1),
    }


def get_flow_stats(runs):
    """Calculate per-flow statistics."""
    flow_stats = {}

    for run in runs:
        for flow in run.get("flows", []):
            flow_name = flow.get("name")
            if not flow_name:
                continue

            if flow_name not in flow_stats:
                flow_stats[flow_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "duration": 0,
                    "retries": 0,
                }

            flow_stats[flow_name]["total"] += 1
            flow_stats[flow_name]["duration"] += flow.get("duration", 0)
            flow_stats[flow_name]["retries"] += flow.get("retries", 0)

            if flow.get("status") == "passed":
                flow_stats[flow_name]["passed"] += 1
            else:
                flow_stats[flow_name]["failed"] += 1

    # Add calculated fields
    for flow_name, stats in flow_stats.items():
        if stats["total"] > 0:
            stats["pass_rate"] = round(stats["passed"] / stats["total"] * 100, 1)
            stats["avg_duration"] = round(stats["duration"] / stats["total"], 1)
        else:
            stats["pass_rate"] = 0
            stats["avg_duration"] = 0

    return flow_stats


def generate_html(runs, metrics, flow_stats):
    """Generate HTML dashboard with Chart.js visualizations."""

    # Prepare data for charts
    labels = [r.get("timestamp", "") for r in runs[-30:]]  # Last 30 runs
    pass_rates = []
    flake_rates = []
    durations = []

    for run in runs[-30:]:
        flows = run.get("flows", [])
        run_passed = sum(1 for f in flows if f.get("status") == "passed")
        run_total = len(flows)

        pass_rates.append(round(run_passed / run_total * 100, 1) if run_total > 0 else 0)
        flake_rates.append(run.get("flake_rate", 0))
        durations.append(run.get("duration", 0))

    # Flow names for flake chart
    flow_names = list(flow_stats.keys())
    flow_pass_rates = [flow_stats[f].get("pass_rate", 0) for f in flow_names]
    flow_durations = [flow_stats[f].get("avg_duration", 0) for f in flow_names]
    flow_retries = [flow_stats[f].get("retries", 0) for f in flow_names]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 32px;
        }}

        .header p {{
            color: #718096;
            font-size: 14px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 8px;
            color: white;
        }}

        .metric-card.success {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}

        .metric-card.warning {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}

        .metric-card.info {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}

        .metric-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}

        .metric-value {{
            font-size: 32px;
            font-weight: bold;
        }}

        .metric-subtext {{
            font-size: 12px;
            opacity: 0.8;
            margin-top: 5px;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }}

        .chart-container h3 {{
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 18px;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        .flow-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .flow-table th {{
            background: #f7fafc;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #e2e8f0;
            color: #2d3748;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }}

        .flow-table td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .flow-table tr:hover {{
            background: #f7fafc;
        }}

        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .status-success {{
            background: #c6f6d5;
            color: #22543d;
        }}

        .status-warning {{
            background: #feebc8;
            color: #7c2d12;
        }}

        .footer {{
            text-align: center;
            color: white;
            font-size: 12px;
            margin-top: 30px;
        }}

        @media (max-width: 1024px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Test Analytics Dashboard</h1>
            <p>Real-time monitoring of mobile test suite health and performance</p>

            <div class="metrics-grid">
                <div class="metric-card success">
                    <div class="metric-label">Pass Rate</div>
                    <div class="metric-value">{metrics['pass_rate']}%</div>
                    <div class="metric-subtext">{metrics['total_runs']} total runs</div>
                </div>
                <div class="metric-card warning">
                    <div class="metric-label">Flake Rate</div>
                    <div class="metric-value">{metrics['flake_rate']}%</div>
                    <div class="metric-subtext">Runs with retries</div>
                </div>
                <div class="metric-card info">
                    <div class="metric-label">Avg Duration</div>
                    <div class="metric-value">{metrics['avg_time']}s</div>
                    <div class="metric-subtext">Per full suite run</div>
                </div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <h3>Pass Rate Trend (Last 30 Runs)</h3>
                <canvas id="passRateChart"></canvas>
            </div>

            <div class="chart-container">
                <h3>Execution Time Trend</h3>
                <canvas id="executionTimeChart"></canvas>
            </div>

            <div class="chart-container">
                <h3>Pass Rate by Flow</h3>
                <canvas id="flowPassRateChart"></canvas>
            </div>

            <div class="chart-container">
                <h3>Retry Count by Flow</h3>
                <canvas id="retryChart"></canvas>
            </div>

            <div class="chart-container full-width">
                <h3>Per-Flow Health Metrics</h3>
                <table class="flow-table">
                    <thead>
                        <tr>
                            <th>Flow</th>
                            <th>Pass Rate</th>
                            <th>Total Runs</th>
                            <th>Failures</th>
                            <th>Avg Duration</th>
                            <th>Total Retries</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for flow_name in flow_names:
        stats = flow_stats[flow_name]
        status_class = "status-success" if stats["pass_rate"] >= 98 else "status-warning"

        html += f"""
                        <tr>
                            <td><strong>{flow_name}</strong></td>
                            <td><span class="status-badge {status_class}">{stats['pass_rate']}%</span></td>
                            <td>{stats['total']}</td>
                            <td>{stats['failed']}</td>
                            <td>{stats['avg_duration']}s</td>
                            <td>{stats['retries']}</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} • Maestro QA Portfolio</p>
        </div>
    </div>

    <script>
        // Chart configuration
        const chartConfig = {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top',
                    labels: {{
                        usePointStyle: true,
                        padding: 15,
                        font: {{
                            size: 12,
                            weight: 500,
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    max: 100,
                    ticks: {{
                        font: {{ size: 11 }},
                        callback: function(value) {{ return value + '%'; }}
                    }}
                }},
                x: {{
                    ticks: {{ font: {{ size: 11 }} }}
                }}
            }}
        }};

        // Pass Rate Trend
        new Chart(document.getElementById('passRateChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([str(i) for i in range(1, len(pass_rates) + 1)])},
                datasets: [{{
                    label: 'Pass Rate (%)',
                    data: {json.dumps(pass_rates)},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                }}]
            }},
            options: {{
                ...chartConfig,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            font: {{ size: 11 }},
                            callback: function(value) {{ return value + '%'; }}
                        }}
                    }}
                }}
            }}
        }});

        // Execution Time Trend
        new Chart(document.getElementById('executionTimeChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps([str(i) for i in range(1, len(durations) + 1)])},
                datasets: [{{
                    label: 'Duration (seconds)',
                    data: {json.dumps(durations)},
                    borderColor: '#f5576c',
                    backgroundColor: 'rgba(245, 87, 108, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#f5576c',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                }}]
            }},
            options: {{
                ...chartConfig,
                scales: {{
                    y: {{
                        ticks: {{
                            font: {{ size: 11 }},
                            callback: function(value) {{ return value + 's'; }}
                        }}
                    }}
                }}
            }}
        }});

        // Flow Pass Rate (Bar Chart)
        new Chart(document.getElementById('flowPassRateChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(flow_names)},
                datasets: [{{
                    label: 'Pass Rate (%)',
                    data: {json.dumps(flow_pass_rates)},
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(245, 87, 108, 0.8)',
                        'rgba(74, 222, 128, 0.8)',
                    ],
                    borderRadius: 8,
                    borderSkipped: false,
                }}]
            }},
            options: {{
                indexAxis: 'y',
                ...chartConfig,
                scales: {{
                    x: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            font: {{ size: 11 }},
                            callback: function(value) {{ return value + '%'; }}
                        }}
                    }},
                    y: {{
                        ticks: {{ font: {{ size: 12 }} }}
                    }}
                }}
            }}
        }});

        // Retry Count (Bar Chart)
        new Chart(document.getElementById('retryChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(flow_names)},
                datasets: [{{
                    label: 'Retry Count',
                    data: {json.dumps(flow_retries)},
                    backgroundColor: 'rgba(250, 112, 154, 0.8)',
                    borderRadius: 8,
                    borderSkipped: false,
                }}]
            }},
            options: {{
                indexAxis: 'y',
                ...chartConfig,
                scales: {{
                    x: {{
                        beginAtZero: true,
                        ticks: {{
                            font: {{ size: 11 }},
                            stepSize: 1,
                        }}
                    }},
                    y: {{
                        ticks: {{ font: {{ size: 12 }} }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    return html


def main():
    """Main function."""
    runs = load_test_runs()
    metrics = calculate_metrics(runs)
    flow_stats = get_flow_stats(runs)

    html = generate_html(runs, metrics, flow_stats)

    # Ensure reports directory exists
    Path("reports").mkdir(exist_ok=True)

    # Write HTML
    output_file = Path("reports/test-dashboard.html")
    with open(output_file, "w") as f:
        f.write(html)

    print(f"✅ Dashboard generated: {output_file}")
    print(f"📊 Metrics: {metrics}")
    print(f"📈 Flows: {list(flow_stats.keys())}")


if __name__ == "__main__":
    main()
