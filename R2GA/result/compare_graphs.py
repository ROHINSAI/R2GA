#!/usr/bin/env python3

import os
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

XLSX_PATH = os.path.join(os.path.dirname(__file__), "Collated Appendix 1.xlsx")

DATASETS = [
    ("Epigenomics", 24),
    ("Epigenomics", 100),
    ("Epigenomics", 997),
    ("Ligo", 30),
    ("Ligo", 100),
    ("Ligo", 1000),
    ("Montage", 25),
    ("Montage", 100),
    ("Montage", 1000),
]

DATASET_LABELS = [f"{w}\n{n}" for w, n in DATASETS]

COL_R2GA_MS = 3
COL_R2GA_ST = 4
COL_HGA_MS  = 5
COL_HGA_ST  = 6
COL_NGA_MS  = 7
COL_NGA_ST  = 8

DATA_START_ROW = 3
RUNS_PER_DATASET = 10


def load_data():
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb.active

    r2ga_ms, hga_ms, nga_ms = [], [], []
    r2ga_st, hga_st, nga_st = [], [], []

    for ds_idx, (workflow, count) in enumerate(DATASETS):
        row_start = DATA_START_ROW + ds_idx * RUNS_PER_DATASET
        row_end   = row_start + RUNS_PER_DATASET

        runs_r2ga_ms, runs_hga_ms, runs_nga_ms = [], [], []
        runs_r2ga_st, runs_hga_st, runs_nga_st = [], [], []

        for row in range(row_start, row_end):
            def v(col):
                val = ws.cell(row=row, column=col).value
                return float(val) if val is not None else 0.0

            runs_r2ga_ms.append(v(COL_R2GA_MS))
            runs_r2ga_st.append(v(COL_R2GA_ST))
            runs_hga_ms.append(v(COL_HGA_MS))
            runs_hga_st.append(v(COL_HGA_ST))
            runs_nga_ms.append(v(COL_NGA_MS))
            runs_nga_st.append(v(COL_NGA_ST))

        r2ga_ms.append(np.mean(runs_r2ga_ms))
        r2ga_st.append(np.mean(runs_r2ga_st))
        hga_ms.append(np.mean(runs_hga_ms))
        hga_st.append(np.mean(runs_hga_st))
        nga_ms.append(np.mean(runs_nga_ms))
        nga_st.append(np.mean(runs_nga_st))

    return (r2ga_ms, hga_ms, nga_ms), (r2ga_st, hga_st, nga_st)


def make_bar_chart(ax, values_list, labels, title, ylabel, colors, algo_names):
    n_datasets = len(DATASET_LABELS)
    n_algos    = len(algo_names)
    bar_width  = 0.22
    group_gap  = 0.08
    total_width = n_algos * bar_width + group_gap

    x = np.arange(n_datasets) * (total_width + 0.12)

    for i, (vals, color, name) in enumerate(zip(values_list, colors, algo_names)):
        offsets = x + i * bar_width - (n_algos - 1) * bar_width / 2
        bars = ax.bar(offsets, vals, width=bar_width, color=color,
                      edgecolor='white', linewidth=0.6, zorder=3, label=name)
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h * 1.008,
                        f'{h:.0f}', ha='center', va='bottom',
                        fontsize=6.5, color='#333333', fontweight='500')

    ax.set_xticks(x)
    ax.set_xticklabels(DATASET_LABELS, fontsize=9, ha='center')
    ax.set_ylabel(ylabel, fontsize=11, labelpad=8)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.legend(fontsize=10, framealpha=0.9, loc='upper left')
    ax.yaxis.grid(True, linestyle='--', alpha=0.55, zorder=0)
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(x[0] - total_width, x[-1] + total_width)


def plot_makespan(ms_data):
    r2ga_ms, hga_ms, nga_ms = ms_data
    colors = ['#2563EB', '#10B981', '#F59E0B']
    algo_names = ['R2GA', 'HGA', 'NGA']

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    make_bar_chart(ax, [r2ga_ms, hga_ms, nga_ms],
                   DATASET_LABELS,
                   'Makespan Comparison — R2GA vs HGA vs NGA',
                   'Average Makespan',
                   colors, algo_names)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(__file__), 'comparison_makespan.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path}")


def plot_scheduling_time(st_data):
    r2ga_st, hga_st, nga_st = st_data
    colors = ['#2563EB', '#10B981', '#F59E0B']
    algo_names = ['R2GA', 'HGA', 'NGA']

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    make_bar_chart(ax, [r2ga_st, hga_st, nga_st],
                   DATASET_LABELS,
                   'Scheduling Time Comparison — R2GA vs HGA vs NGA',
                   'Average Scheduling Time (s)',
                   colors, algo_names)

    plt.tight_layout()
    out_path = os.path.join(os.path.dirname(__file__), 'comparison_scheduling_time.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path}")


def main():
    print("Loading data from Collated Appendix 1.xlsx ...")
    ms_data, st_data = load_data()
    print("Plotting makespan comparison ...")
    plot_makespan(ms_data)
    print("Plotting scheduling time comparison ...")
    plot_scheduling_time(st_data)
    print("Done.")


if __name__ == '__main__':
    main()
