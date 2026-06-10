#!/bin/bash

./visuals/generate_both_reports.sh
./visuals/innodb_metrics_report.py benchmark_logs
./visuals/vars_comparison_report.py benchmark_logs .
./visuals/generate_index.py .