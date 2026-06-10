#!/bin/bash


# sudo apt update
# sudo apt install sysstat sysbench dstat -y

# 2. Set CPU governor to performance mode and disable CPU idle state
log_info "Setting CPU governor to performance mode..."
sudo cpupower frequency-set -g performance 2>/dev/null || log_warn "Could not set CPU governor (cpupower not available or insufficient permissions)"

log_info "Disabling CPU idle states..."
for cpu_idle in /sys/devices/system/cpu/cpu*/cpuidle/state*/disable; do
    if [ -f "$cpu_idle" ]; then
        echo 1 | sudo tee "$cpu_idle" > /dev/null 2>&1 || true
    fi
done


./run_pt_summary.sh
./run_pt_mysql_summary.sh

./run_metrics.sh "$1" "$2"

# ./run_metrics.sh "percona-server" "8.4.8" "0"


echo ""
echo "=========================================================================="
echo "All benchmarks completed!"
echo "=========================================================================="