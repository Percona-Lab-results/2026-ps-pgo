#!/usr/bin/env python3
"""
vars_comparison_report.py

Generates HTML comparison reports for MySQL status and system variables across tiers.
Compares multiple servers side-by-side for Tier2G, Tier12G, and Tier32G.

Usage:
  python3 vars_comparison_report.py [base_dir] [output_dir]

Defaults:
  base_dir   = "./benchmark_logs"
  output_dir = "."
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


def parse_variables_file(path: str) -> Dict[str, str]:
    """Parse a status or variables file (key-value pairs)."""
    variables = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or '\t' not in line:
                    continue
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    key, value = parts
                    variables[key] = value
    except Exception as e:
        print(f"Warning: Failed to read {path}: {e}")
    return variables


def find_variable_files(base_dir: str, file_type: str, tier: str) -> Dict[str, Dict[str, str]]:
    """
    Find all Tier{X}G.{type}.txt files for a specific tier.
    Returns dict: {'mysql 9.7.0': {...}, 'mysql-non-pgo 9.7.0': {...}}
    """
    result = {}
    base_path = Path(base_dir)
    pattern = f"**/{tier}.{file_type}.txt"

    for path in base_path.glob(pattern):
        parts = path.parts
        if len(parts) < 4:
            continue

        db_type = parts[-3]
        version = parts[-2]
        server_name = f"{db_type} {version}"

        variables = parse_variables_file(str(path))
        result[server_name] = variables

    return result


def generate_html_report(data_by_tier: Dict[str, Dict[str, Dict[str, str]]],
                         output_path: str,
                         report_type: str,
                         tiers: List[str]):
    """Generate HTML comparison report."""

    # Collect all unique servers across all tiers
    all_servers = set()
    for tier_data in data_by_tier.values():
        all_servers.update(tier_data.keys())
    servers = sorted(all_servers)

    # Collect all variable names across all tiers
    all_vars: Set[str] = set()
    for tier in tiers:
        for server_data in data_by_tier[tier].values():
            all_vars.update(server_data.keys())

    all_vars = sorted(all_vars)

    # Count variables
    total_vars = len(all_vars)

    # Build HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{report_type.title()} Variables Comparison - Per Tier</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            margin-top: 0;
            color: #1a73e8;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #1a73e8;
        }}
        .stat-box .label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-box .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
        .controls {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .controls label {{
            font-weight: 600;
            color: #333;
        }}
        .controls input {{
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
            flex: 1;
            min-width: 250px;
        }}
        .controls select {{
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
        }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }}
        .count-badge {{
            background: #1a73e8;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            table-layout: fixed;
            min-width: 0;
        }}
        th {{
            background: #1a73e8;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
            word-break: break-all;
            overflow-wrap: anywhere;
        }}
        .var-name {{
            font-weight: 500;
            color: #333;
        }}
        .value-cell {{
            font-family: 'Courier New', monospace;
            color: #555;
            font-size: 11px;
        }}
        .var-row.hidden {{
            display: none;
        }}
        .different {{
            background: #fff3cd !important;
        }}
        .var-row:hover {{
            background: #f8f9fa;
        }}
        .different:hover {{
            background: #ffe69c !important;
        }}
        .badge {{
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 8px;
        }}
        .badge-diff {{
            background: #ffc107;
            color: #000;
        }}
        .tier-section {{
            margin-bottom: 30px;
            display: none;
        }}
        .tier-section.active {{
            display: block;
        }}
        .tier-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 6px 6px 0 0;
            font-size: 18px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <h1>{report_type.title()} Variables Comparison - Tier 2G, 12G, 32G</h1>

    <div class="summary">
        <h2>Overview</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="label">Total Variables</div>
                <div class="value">{total_vars}</div>
            </div>
            <div class="stat-box">
                <div class="label">Servers</div>
                <div class="value">{len(servers)}</div>
            </div>
            <div class="stat-box">
                <div class="label">Tiers</div>
                <div class="value">{len(tiers)}</div>
            </div>
        </div>
        <p><strong>Servers:</strong></p>
        <ul>
'''

    for server in servers:
        html += f'            <li><strong>{server}</strong></li>\n'

    html += '''        </ul>
    </div>

    <div class="controls">
        <label for="tierSelect">Select Tier:</label>
        <select id="tierSelect">
'''

    for tier in tiers:
        selected = ' selected' if tier == 'Tier12G' else ''
        html += f'            <option value="{tier}"{selected}>{tier}</option>\n'

    html += '''        </select>

        <label for="search">Search variables:</label>
        <input type="text" id="search" placeholder="Type to filter variables (e.g., innodb, buffer, thread)">

        <label for="filter">Filter:</label>
        <select id="filter">
            <option value="all">All Variables</option>
            <option value="different">Variables with Different Values</option>
            <option value="same">Variables with Same Values</option>
        </select>
    </div>
'''

    # Generate a section for each tier
    for i, tier in enumerate(tiers):
        tier_data = data_by_tier[tier]
        active_class = "active" if tier == 'Tier12G' else ""

        html += f'''
    <div class="section tier-section {active_class}" data-tier="{tier}">
        <div class="tier-header">{tier} Configuration</div>
        <h2>All {report_type.title()} Variables <span class="count-badge" id="visibleCount-{tier}">{total_vars} variables</span></h2>
        <table class="tier-table" data-tier="{tier}">
            <thead>
                <tr>
                    <th style="width: 25%">Variable Name</th>
'''

        for server in servers:
            width = 75 // len(servers)
            html += f'                    <th style="width: {width}%">{server}</th>\n'

        html += '''                </tr>
            </thead>
            <tbody>
'''

        for var in all_vars:
            values = []
            for server in servers:
                value = tier_data.get(server, {}).get(var, 'N/A')
                values.append(value)

            # Check if values differ
            unique_values = set(values)
            # If we have N/A and something else, it's different
            # If all values are the same (including all N/A), it's same
            is_different = len(unique_values) > 1
            category = "different" if is_different else "same"
            row_class = "var-row different" if is_different else "var-row"

            html += f'                <tr class="{row_class}" data-var="{var.lower()}" data-category="{category}">\n'

            var_name_html = var
            if is_different:
                var_name_html += '<span class="badge badge-diff">DIFFERENT</span>'

            html += f'                    <td class="var-name">{var_name_html}</td>\n'

            for value in values:
                html += f'                    <td class="value-cell">{value}</td>\n'

            html += '                </tr>\n'

        html += '''            </tbody>
        </table>
    </div>
'''

    html += '''
    <script>
        const tierSelect = document.getElementById('tierSelect');
        const searchInput = document.getElementById('search');
        const filterSelect = document.getElementById('filter');
        const tierSections = document.querySelectorAll('.tier-section');
        const tables = document.querySelectorAll('.tier-table');

        function showTier(selectedTier) {
            tierSections.forEach(section => {
                if (section.dataset.tier === selectedTier) {
                    section.classList.add('active');
                } else {
                    section.classList.remove('active');
                }
            });
            applyFilters();
        }

        function applyFilters() {
            const searchTerm = searchInput.value.toLowerCase();
            const filterValue = filterSelect.value;
            const selectedTier = tierSelect.value;

            tables.forEach(table => {
                const tier = table.dataset.tier;
                if (tier !== selectedTier) return;

                const rows = table.querySelectorAll('.var-row');
                const badge = document.getElementById('visibleCount-' + tier);
                let visibleCount = 0;

                rows.forEach(row => {
                    const varName = row.dataset.var;
                    const category = row.dataset.category;

                    const matchesSearch = !searchTerm || varName.includes(searchTerm);

                    let matchesFilter = true;
                    if (filterValue === 'same') {
                        matchesFilter = category === 'same';
                    } else if (filterValue === 'different') {
                        matchesFilter = category === 'different';
                    }

                    if (matchesSearch && matchesFilter) {
                        row.classList.remove('hidden');
                        visibleCount++;
                    } else {
                        row.classList.add('hidden');
                    }
                });

                badge.textContent = visibleCount + ' variables';
            });
        }

        tierSelect.addEventListener('change', function() {
            showTier(this.value);
        });

        searchInput.addEventListener('input', applyFilters);
        filterSelect.addEventListener('change', applyFilters);

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            showTier(tierSelect.value);
        });
    </script>
</body>
</html>
'''

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ Generated: {output_path}")


def main():
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "../benchmark_logs"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else ".."

    tiers = ['Tier2G', 'Tier12G', 'Tier32G']

    print("Scanning for status and variables files...")

    for file_type, report_name in [('status', 'status_variables_comparison.html'),
                                    ('vars', 'system_variables_comparison.html')]:

        data_by_tier = {}
        found_any = False

        for tier in tiers:
            tier_data = find_variable_files(base_dir, file_type, tier)
            if tier_data:
                data_by_tier[tier] = tier_data
                found_any = True
                print(f"  {tier}: Found {len(tier_data)} servers")

        if found_any:
            if file_type == "status":
                report_type = "status"
            elif file_type == "vars":
                report_type = "system"
            else:
                report_type = file_type
            output_path = os.path.join(output_dir, report_name)
            generate_html_report(data_by_tier, output_path, report_type, tiers)
        else:
            print(f"  No {file_type} files found")

    print("\n✓ Report generation complete!")


if __name__ == "__main__":
    main()
