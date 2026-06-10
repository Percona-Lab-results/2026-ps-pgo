#!/usr/bin/env python3
"""
generate_index.py

Generates the main index.html page with links to all available reports.

Usage:
  python3 generate_index.py [output_dir]

Defaults:
  output_dir = "."
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple


def get_file_size(path: str) -> str:
    """Get human-readable file size."""
    size = os.path.getsize(path)
    for unit in ['', 'K', 'M', 'G']:
        if size < 1024.0:
            return f"{int(size)}{unit}"
        size /= 1024.0
    return f"{int(size)}T"


def find_reports(base_dir: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Find all HTML report files and categorize them.
    Returns dict of categories with report info.
    """
    base_path = Path(base_dir)

    # Define report categories and patterns
    reports = {
        'performance': [],
        'variables': []
    }

    # Map of report patterns to metadata
    report_metadata = {
        'sysbench_ps_mysql_individual.html': {
            'title': 'Sysbench Individual Runs',
            'icon': '📉',
            'description': 'Detailed view of each benchmark run with per-run performance breakdown and statistics.',
            'category': 'performance',
            'type': 'Performance'
        },
        'sysbench_ps_mysql_average.html': {
            'title': 'Sysbench Average Results',
            'icon': '📈',
            'description': 'Aggregated performance metrics across all benchmark runs showing average throughput and latency.',
            'category': 'performance',
            'type': 'Performance'
        },
        'innodb_metrics_report.html': {
            'title': 'InnoDB Metrics',
            'icon': '💾',
            'description': 'Interactive InnoDB storage engine metrics with multi-select controls for servers and runs.',
            'category': 'performance',
            'type': 'Storage'
        },
        'status_variables_comparison.html': {
            'title': 'Status Variables',
            'icon': '📊',
            'description': 'Comparison of MySQL status variables across servers with filtering and search capabilities.',
            'category': 'variables',
            'type': 'Variables'
        },
        'system_variables_comparison.html': {
            'title': 'System Variables',
            'icon': '⚙️',
            'description': 'Side-by-side comparison of MySQL system configuration variables and their values.',
            'category': 'variables',
            'type': 'Configuration'
        }
    }

    # Scan for reports
    for filename, metadata in report_metadata.items():
        filepath = base_path / filename
        if filepath.exists():
            report = {
                'filename': filename,
                'title': metadata['title'],
                'icon': metadata['icon'],
                'description': metadata['description'],
                'type': metadata['type'],
                'size': get_file_size(str(filepath))
            }
            reports[metadata['category']].append(report)

    return reports


def generate_index_html(reports: Dict[str, List[Dict[str, str]]], output_path: str):
    """Generate index.html with links to all reports."""

    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MySQL 9.7.0 PGO Benchmark Reports</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: system-ui, -apple-system, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }

        h1 {
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .subtitle {
            font-size: 18px;
            opacity: 0.95;
        }

        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }

        .report-card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-decoration: none;
            color: inherit;
            display: block;
        }

        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .report-card h2 {
            color: #1a73e8;
            font-size: 24px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .report-card .icon {
            font-size: 28px;
        }

        .report-card p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }

        .report-card .meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }

        .badge {
            background: #f0f0f0;
            color: #666;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }

        .badge.size {
            background: #e3f2fd;
            color: #1976d2;
        }

        .badge.type {
            background: #f3e5f5;
            color: #7b1fa2;
        }

        .section-title {
            color: white;
            font-size: 28px;
            font-weight: 600;
            margin: 40px 0 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }

        .arrow {
            margin-left: auto;
            font-size: 20px;
            color: #1a73e8;
        }

        footer {
            text-align: center;
            color: white;
            margin-top: 60px;
            opacity: 0.8;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MySQL 9.7.0 PGO Benchmarks</h1>
            <div class="subtitle">Performance comparison: mysql vs mysql-non-pgo</div>
        </header>
'''

    # Performance Reports Section
    if reports['performance']:
        html += '''
        <div class="section-title">📊 Performance Reports</div>
        <div class="reports-grid">
'''
        for report in reports['performance']:
            html += f'''
            <a href="{report['filename']}" class="report-card">
                <h2><span class="icon">{report['icon']}</span>{report['title']}</h2>
                <p>{report['description']}</p>
                <div class="meta">
                    <span class="badge type">{report['type']}</span>
                    <span class="badge size">{report['size']}</span>
                    <span class="arrow">→</span>
                </div>
            </a>
'''
        html += '''        </div>
'''

    # Variable Comparisons Section
    if reports['variables']:
        html += '''
        <div class="section-title">🔍 Variable Comparisons</div>
        <div class="reports-grid">
'''
        for report in reports['variables']:
            html += f'''
            <a href="{report['filename']}" class="report-card">
                <h2><span class="icon">{report['icon']}</span>{report['title']}</h2>
                <p>{report['description']}</p>
                <div class="meta">
                    <span class="badge type">{report['type']}</span>
                    <span class="badge size">{report['size']}</span>
                    <span class="arrow">→</span>
                </div>
            </a>
'''
        html += '''        </div>
'''

    html += '''
        <footer>
            <p>Generated reports for MySQL 9.7.0 PGO benchmark analysis</p>
            <p>Tier configurations: 2G, 12G, 32G | Servers: mysql, mysql-non-pgo</p>
        </footer>
    </div>
</body>
</html>
'''

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ Generated: {output_path}")


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else ".."

    print("Scanning for HTML reports...")
    reports = find_reports(output_dir)

    total_reports = len(reports['performance']) + len(reports['variables'])
    print(f"Found {total_reports} reports:")
    print(f"  Performance: {len(reports['performance'])}")
    print(f"  Variables: {len(reports['variables'])}")

    output_path = os.path.join(output_dir, "index.html")
    generate_index_html(reports, output_path)

    print("\n✓ Index generation complete!")


if __name__ == "__main__":
    main()
