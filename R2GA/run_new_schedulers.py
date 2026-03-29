"""
run_new_schedulers.py
Run GeneticScheduler1, HGAScheduler1, NGAScheduler1 on three datasets and
collect makespan, system utilisation, workload balance, and energy.
Results are saved to result/new_metrics_results.json for the plotting script.
"""

import os, sys, time, json

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── silence the Windows-path Logger side-effect ──────────────────────────────
import builtins as _builtins
_real_open = _builtins.open
def _safe_open(file, mode='r', *args, **kwargs):
    if isinstance(file, str) and 'result_task.html' in file:
        return _real_open(os.devnull, mode, *args, **kwargs)
    return _real_open(file, mode, *args, **kwargs)
_builtins.open = _safe_open

from COMPONENT.application import Application
from system.computingsystem import ComputingSystem
from service.applicationservice import ApplicationService
from UTIL.genericutils import readfile
from SCHEDULER.task.geneticscheduler1 import GeneticScheduler1
from SCHEDULER.task.HGAscheduler1 import HGAScheduler1
from SCHEDULER.task.NGAscheduler1 import NGAScheduler1

_builtins.open = _real_open

# ── configuration ─────────────────────────────────────────────────────────────
PROCESSOR_NUMBER = 6
MAX_ITERATIONS   = 30   # increase to 300 for full quality

DATASETS = [
    ("Epigenomics-24", os.path.join(ROOT, "Epigenomics_24_0.xml")),
    ("Ligo-30",        os.path.join(ROOT, "Ligo_30_0.xml")),
    ("Montage-25",     os.path.join(ROOT, "Montage_25_0.xml")),
]

ALGORITHMS = [
    ("GeneticScheduler1", GeneticScheduler1, "GeneticScheduler1"),
    ("HGAScheduler1",     HGAScheduler1,     "HGAScheduler1"),
    ("NGAScheduler1",     NGAScheduler1,     "NGAScheduler1"),
]


def _reset():
    ComputingSystem.processors.clear()
    ComputingSystem.applications.clear()
    ComputingSystem.VRFs.clear()
    ComputingSystem.processors1.clear()
    ComputingSystem.init_flag = False
    ComputingSystem.instance  = None


def run_algorithm(algo_name, SchedulerClass, sched_label, xml_path):
    _reset()
    ComputingSystem.init(PROCESSOR_NUMBER)

    computation_time_matrix, communication_time_matrix = readfile(xml_path)
    task_number = len(computation_time_matrix)

    app = Application(name=os.path.basename(xml_path))
    ApplicationService.init_application(
        type('S', (), {'scheduler_name': sched_label})(),
        app,
        task_number,
        computation_time_matrix,
        None,
        communication_time_matrix,
    )

    scheduler = SchedulerClass(sched_label)

    makespan, _cost, system_util, workload_balance, energy = scheduler.schedule(
        sign        = 0,
        app         = app,
        outfilename = 'Appendix 1.txt',
        target      = MAX_ITERATIONS,
        st          = time.time(),
    )
    return makespan, system_util, workload_balance, energy


def main():
    _devnull = open(os.devnull, 'w')
    results = {}   # results[ds_label][algo_name] = dict of metrics

    print("\n" + "=" * 72)
    print("  GeneticScheduler1 vs HGAScheduler1 vs NGAScheduler1 — 4-Metric Comparison")
    print("=" * 72)

    for ds_label, xml_path in DATASETS:
        results[ds_label] = {}
        print(f"\n  Dataset: {ds_label}")
        print(f"  {'Algorithm':<20}  {'Makespan':>10}  {'Utilization':>12}  {'WL Balance':>11}  {'Energy':>10}  {'Time':>8}")
        print(f"  {'-'*20}  {'-'*10}  {'-'*12}  {'-'*11}  {'-'*10}  {'-'*8}")

        for algo_name, SchedulerClass, sched_label in ALGORITHMS:
            t0 = time.time()
            sys.stdout = _devnull
            try:
                ms, util, wb, eng = run_algorithm(algo_name, SchedulerClass, sched_label, xml_path)
            finally:
                sys.stdout = sys.__stdout__
            elapsed = time.time() - t0
            results[ds_label][algo_name] = {
                "makespan":          ms,
                "system_util":       util,
                "workload_balance":  wb,
                "energy":            eng,
            }
            print(f"  {algo_name:<20}  {ms:>10.2f}  {util:>12.4f}  {wb:>11.2f}  {eng:>10.2f}  {elapsed:>7.2f}s")

    _devnull.close()

    # Save results for plotting
    out_dir = os.path.join(ROOT, "result")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "new_metrics_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {json_path}")
    print()


if __name__ == "__main__":
    main()
