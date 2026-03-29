"""
test.py – Run R2GA, HGA, NGA on Epigenomics_24, Ligo_30, Montage_25
          and print a side-by-side makespan comparison table.
"""

import os
import sys
import time

# ── make project root importable ──────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Silence the Logger redirect that tries to open a Windows path
import UTIL.logger as _lg
class _StdoutLogger:
    """Thin wrapper that keeps everything on sys.__stdout__."""
    def write(self, msg):
        sys.__stdout__.write(msg)
    def flush(self):
        sys.__stdout__.flush()

# Patch before scheduler classes are imported to avoid file-open side-effects
import builtins as _builtins
_real_open = _builtins.open
def _safe_open(file, mode='r', *args, **kwargs):
    # intercept the Windows log-file open and redirect to devnull
    if isinstance(file, str) and 'result_task.html' in file:
        return _real_open(os.devnull, mode, *args, **kwargs)
    return _real_open(file, mode, *args, **kwargs)
_builtins.open = _safe_open

# ── project imports ────────────────────────────────────────────────────────────
from COMPONENT.application import Application
from system.computingsystem import ComputingSystem
from service.applicationservice import ApplicationService
from UTIL.genericutils import readfile
from SCHEDULER.task.geneticscheduler import GeneticScheduler
from SCHEDULER.task.HGAscheduler import HGAScheduler
from SCHEDULER.task.NGAscheduler import NGAScheduler

# Restore open
_builtins.open = _real_open

# ── configuration ──────────────────────────────────────────────────────────────
PROCESSOR_NUMBER = 6        # 6 heterogeneous processors (matching the readfile matrix width)
MAX_ITERATIONS   = 30       # kept low for a quick demo; raise to 300 for full quality

DATASETS = [
    ("Epigenomics-24",  os.path.join(ROOT, "Epigenomics_24_0.xml")),
    ("Ligo-30",         os.path.join(ROOT, "Ligo_30_0.xml")),
    ("Montage-25",      os.path.join(ROOT, "Montage_25_0.xml")),
]

ALGORITHMS = [
    ("R2GA", GeneticScheduler, "R2GA"),
    ("HGA",  HGAScheduler,     "HGA"),
    ("NGA",  NGAScheduler,     "NGA"),
]

# ── helpers ────────────────────────────────────────────────────────────────────

def _reset_computing_system():
    """Full reset of the ComputingSystem singleton between runs."""
    ComputingSystem.processors.clear()
    ComputingSystem.applications.clear()
    ComputingSystem.VRFs.clear()
    ComputingSystem.processors1.clear()
    ComputingSystem.init_flag = False
    ComputingSystem.instance  = None


def run_algorithm(algo_name, SchedulerClass, scheduler_label, xml_path):
    """
    Initialise a fresh ComputingSystem + Application, then run the scheduler.
    Returns the best makespan (float).
    """
    _reset_computing_system()
    ComputingSystem.init(PROCESSOR_NUMBER)

    computation_time_matrix, communication_time_matrix = readfile(xml_path)
    task_number = len(computation_time_matrix)

    app = Application(name=os.path.basename(xml_path))
    ApplicationService.init_application(
        type('S', (), {'scheduler_name': scheduler_label})(),
        app,
        task_number,
        computation_time_matrix,
        None,                       # no cost matrix needed
        communication_time_matrix,
    )

    scheduler = SchedulerClass(scheduler_label)

    # 'Appendix 1.txt' mode runs exactly MAX_ITERATIONS iterations
    makespan, _cost = scheduler.schedule(
        sign        = 0,
        app         = app,
        outfilename = 'Appendix 1.txt',
        target      = MAX_ITERATIONS,
        st          = time.time(),
    )
    return makespan


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    # Suppress verbose prints from the schedulers
    _devnull = open(os.devnull, 'w')

    results = {}   # results[dataset_label][algo_name] = makespan

    print()
    print("=" * 62)
    print("  R2GA vs HGA vs NGA  –  Makespan Comparison")
    print("=" * 62)

    for ds_label, xml_path in DATASETS:
        results[ds_label] = {}
        print(f"\n  Dataset: {ds_label}")
        print(f"  {'Algorithm':<10}  {'Makespan':>12}  {'Time (s)':>10}")
        print(f"  {'-'*10}  {'-'*12}  {'-'*10}")
        for algo_name, SchedulerClass, sched_label in ALGORITHMS:
            t0 = time.time()
            # redirect stdout during the algorithm run to suppress internal prints
            sys.stdout = _devnull
            try:
                ms = run_algorithm(algo_name, SchedulerClass, sched_label, xml_path)
            finally:
                sys.stdout = sys.__stdout__
            elapsed = time.time() - t0
            results[ds_label][algo_name] = ms
            print(f"  {algo_name:<10}  {ms:>12.2f}  {elapsed:>10.2f}s")

    _devnull.close()

    # ── summary table ──────────────────────────────────────────────────────────
    algo_names = [a[0] for a in ALGORITHMS]
    ds_labels  = [d[0] for d in DATASETS]
    col_w      = 14

    print()
    print("=" * (18 + col_w * len(algo_names)))
    print("  SUMMARY TABLE  –  Best Makespan per Algorithm")
    print("=" * (18 + col_w * len(algo_names)))
    header = f"  {'Dataset':<16}" + "".join(f"{a:>{col_w}}" for a in algo_names)
    print(header)
    print("  " + "-" * (16 + col_w * len(algo_names)))

    for ds in ds_labels:
        row = f"  {ds:<16}"
        best_ms = min(results[ds].values())
        for algo in algo_names:
            ms  = results[ds][algo]
            tag = " ★" if ms == best_ms else ""
            row += f"{ms:>{col_w-2}.2f}{tag:>2}"
        print(row)

    print()
    print("  ★ = best (lowest) makespan for that dataset")
    print()


if __name__ == "__main__":
    main()
