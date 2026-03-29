"""
plot_new_comparison.py
Reads result/new_metrics_results.json (produced by run_new_schedulers.py)
and saves four bar-chart PNG files to result/:
  1. comparison_new_makespan.png
  2. comparison_system_utilization.png
  3. comparison_workload_balance.png
  4. comparison_energy_consumption.png
"""

import os, sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT     = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(ROOT, "result")
JSON_PATH = os.path.join(OUT_DIR, "new_metrics_results.json")

DATASETS = ["Epigenomics-24", "Ligo-30", "Montage-25"]
ALGOS    = ["GeneticScheduler1", "HGAScheduler1", "NGAScheduler1"]
ALGO_SHORT = ["Genetic1", "HGA1", "NGA1"]

COLORS = ["#2563EB", "#10B981", "#F59E0B"]

# ── chart helper ──────────────────────────────────────────────────────────────

def _bar_chart(values_by_algo, title, ylabel, filename, higher_is_better=False):
    """
    values_by_algo : list of lists, shape [n_algos][n_datasets]
    """
    n_ds    = len(DATASETS)
    n_algo  = len(ALGOS)
    bw      = 0.22
    gap     = 0.10
    total_w = n_algo * bw + gap
    x = np.arange(n_ds) * (total_w + 0.14)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    for i, (vals, color, short) in enumerate(zip(values_by_algo, COLORS, ALGO_SHORT)):
        offsets = x + i * bw - (n_algo - 1) * bw / 2
        bars = ax.bar(offsets, vals, width=bw, color=color,
                      edgecolor='white', linewidth=0.7, zorder=3, label=short)
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                fmt = f'{h:.3f}' if h < 1 else f'{h:.1f}'
                ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01,
                        fmt, ha='center', va='bottom',
                        fontsize=7, color='#222222', fontweight='500')

    ax.set_xticks(x)
    ax.set_xticklabels(DATASETS, fontsize=10, ha='center')
    ax.set_ylabel(ylabel, fontsize=11, labelpad=8)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=14)
    ax.legend(fontsize=10, framealpha=0.9, loc='upper right')
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(x[0] - total_w, x[-1] + total_w)
    if higher_is_better:
        ax.set_ylim(0, max(max(v) for v in values_by_algo) * 1.18)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, filename)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(JSON_PATH):
        print(f"[ERROR] Results file not found: {JSON_PATH}")
        print("  Run  python run_new_schedulers.py  first.")
        sys.exit(1)

    with open(JSON_PATH) as f:
        data = json.load(f)

    # Build shape [n_algos][n_datasets] for each metric
    def extract(metric):
        return [
            [data[ds][algo][metric] for ds in DATASETS]
            for algo in ALGOS
        ]

    makespan_vals  = extract("makespan")
    util_vals      = extract("system_util")
    wb_vals        = extract("workload_balance")
    energy_vals    = extract("energy")

    os.makedirs(OUT_DIR, exist_ok=True)
    print("\nGenerating comparison plots …\n")

    _bar_chart(
        makespan_vals,
        title  = "Makespan Comparison — GeneticScheduler1 vs HGAScheduler1 vs NGAScheduler1",
        ylabel = "Makespan (time units)",
        filename = "comparison_new_makespan.png",
    )

    _bar_chart(
        util_vals,
        title  = "System Utilization — GeneticScheduler1 vs HGAScheduler1 vs NGAScheduler1",
        ylabel = "System Utilization (0–1, higher = better)",
        filename = "comparison_system_utilization.png",
        higher_is_better = True,
    )

    _bar_chart(
        wb_vals,
        title  = "Workload Balance — GeneticScheduler1 vs HGAScheduler1 vs NGAScheduler1",
        ylabel = "Workload Imbalance (max_ft − min_ft, lower = better)",
        filename = "comparison_workload_balance.png",
    )

    _bar_chart(
        energy_vals,
        title  = "Energy Consumption — GeneticScheduler1 vs HGAScheduler1 vs NGAScheduler1",
        ylabel = "Energy (duration × speed_factor, lower = better)",
        filename = "comparison_energy_consumption.png",
    )

    print("\nAll 4 plots saved to result/\n")


if __name__ == "__main__":
    main()
