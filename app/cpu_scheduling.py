"""
cpu_scheduling.py
==================

Implements:
  - FCFS                      (First Come First Served)
  - SJF (Non-Preemptive)      (Shortest Job First)
  - SRTF                      (Shortest Remaining Time First / preemptive SJF)
  - Priority (Non-Preemptive)
  - Priority (Preemptive)
  - Round Robin

Every algorithm returns:
  (processes, schedule)
    processes -> list[Process] with completion/turnaround/waiting/response times filled in
    schedule  -> list[(pid, start_time, end_time)] segments, ready for a Gantt chart
"""

import copy
from dataclasses import dataclass, field
from typing import List


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0          # makes lower number = higher priority
    remaining_time: int = field(init=False)
    completion_time: int = 0
    turnaround_time: int = 0
    waiting_time: int = 0
    response_time: int = -1

    def __post_init__(self):
        self.remaining_time = self.burst_time


def _reset(processes: List[Process]) -> List[Process]:
    """Deep-copy and reset runtime fields so the same input list can be reused
    across multiple algorithms without side effects."""
    fresh = copy.deepcopy(processes)
    for p in fresh:
        p.remaining_time = p.burst_time
        p.completion_time = 0
        p.turnaround_time = 0
        p.waiting_time = 0
        p.response_time = -1
    return fresh


def _compute_metrics(processes: List[Process]) -> List[Process]:
    for p in processes:
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
    return processes


def _merge_segments(raw_schedule):
    """Merge consecutive 1-unit ticks belonging to the same process into a
    single contiguous Gantt-chart segment."""
    if not raw_schedule:
        return []
    merged = [list(raw_schedule[0])]
    for pid, s, e in raw_schedule[1:]:
        if pid == merged[-1][0] and s == merged[-1][2]:
            merged[-1][2] = e
        else:
            merged.append([pid, s, e])
    return [tuple(x) for x in merged]


def _time_step_schedule(processes: List[Process], select_fn, preemptive=True):
    """
    Generic 1-unit-at-a-time simulator.

    select_fn(ready_list, all_processes, current_time) -> chosen Process

    preemptive=True  -> select_fn is re-evaluated EVERY tick (SRTF, Priority-P)
    preemptive=False -> once a process is chosen it runs to completion before
                         select_fn is consulted again (FCFS, SJF-NP, Priority-NP)
    """
    procs = _reset(processes)
    n = len(procs)
    time = 0
    completed = 0
    raw_schedule = []
    current = None

    # safety cap to avoid infinite loops on bad input
    max_time = sum(p.burst_time for p in procs) + max((p.arrival_time for p in procs), default=0) + 10

    while completed < n and time < max_time:
        ready = [p for p in procs if p.arrival_time <= time and p.remaining_time > 0]

        if not ready:
            time += 1
            current = None
            continue

        if preemptive or current is None or current.remaining_time == 0:
            current = select_fn(ready, procs, time)

        p = current
        if p.response_time == -1:
            p.response_time = time - p.arrival_time

        raw_schedule.append((p.pid, time, time + 1))
        p.remaining_time -= 1
        time += 1

        if p.remaining_time == 0:
            p.completion_time = time
            completed += 1
            current = None

    _compute_metrics(procs)
    return procs, _merge_segments(raw_schedule)


# ---------------------------------------------------------------------------
# Algorithms
# ---------------------------------------------------------------------------

def fcfs(processes: List[Process]):
    sel = lambda ready, procs, t: min(ready, key=lambda p: (p.arrival_time, p.pid))
    return _time_step_schedule(processes, sel, preemptive=False)


def sjf_non_preemptive(processes: List[Process]):
    sel = lambda ready, procs, t: min(ready, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
    return _time_step_schedule(processes, sel, preemptive=False)


def srtf(processes: List[Process]):
    """Shortest Remaining Time First = preemptive SJF."""
    sel = lambda ready, procs, t: min(ready, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
    return _time_step_schedule(processes, sel, preemptive=True)


def priority_non_preemptive(processes: List[Process]):
    sel = lambda ready, procs, t: min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid))
    return _time_step_schedule(processes, sel, preemptive=False)


def priority_preemptive(processes: List[Process]):
    sel = lambda ready, procs, t: min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid))
    return _time_step_schedule(processes, sel, preemptive=True)


def round_robin(processes: List[Process], quantum: int = 2):
    procs = _reset(processes)
    n = len(procs)
    procs_sorted = sorted(procs, key=lambda p: (p.arrival_time, p.pid))

    time = 0
    queue: List[Process] = []
    raw_schedule = []
    completed = 0
    arrived_idx = 0

    def push_arrivals(curr_time):
        nonlocal arrived_idx
        while arrived_idx < n and procs_sorted[arrived_idx].arrival_time <= curr_time:
            queue.append(procs_sorted[arrived_idx])
            arrived_idx += 1

    push_arrivals(time)
    if not queue and arrived_idx < n:
        time = procs_sorted[0].arrival_time
        push_arrivals(time)

    while completed < n:
        if not queue:
            if arrived_idx < n:
                time = procs_sorted[arrived_idx].arrival_time
                push_arrivals(time)
            continue

        p = queue.pop(0)
        if p.response_time == -1:
            p.response_time = time - p.arrival_time

        run_time = min(quantum, p.remaining_time)
        start = time
        time += run_time
        p.remaining_time -= run_time
        raw_schedule.append((p.pid, start, time))

        push_arrivals(time)

        if p.remaining_time > 0:
            queue.append(p)
        else:
            p.completion_time = time
            completed += 1

    _compute_metrics(procs)
    return procs, _merge_segments(raw_schedule)


ALGORITHMS = {
    "FCFS": fcfs,
    "SJF (Non-Preemptive)": sjf_non_preemptive,
    "SRTF (SJF Preemptive)": srtf,
    "Priority (Non-Preemptive)": priority_non_preemptive,
    "Priority (Preemptive)": priority_preemptive,
    # round_robin excluded here because it needs an extra `quantum` argument
}
