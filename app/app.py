"""
app.py
======
OS Simulator — Flask backend.

    cpu_scheduling.py
    memory_management.py
    virtual_memory.py
    disk_scheduling.py

The frontend renders every result as an interactive "trace" visualization in the browser.
This keeps results fully interactive.

"""

from flask import Flask, render_template, request, jsonify

import cpu_scheduling as cpu
import memory_management as mem
import virtual_memory as vm
import disk_scheduling as disk

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def error(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def process_table(procs):
    rows = []
    for p in sorted(procs, key=lambda x: x.pid):
        rows.append({
            "pid": p.pid,
            "arrival_time": p.arrival_time,
            "burst_time": p.burst_time,
            "priority": p.priority,
            "completion_time": p.completion_time,
            "turnaround_time": p.turnaround_time,
            "waiting_time": p.waiting_time,
            "response_time": p.response_time,
        })
    n = len(procs)
    avg_tat = sum(p.turnaround_time for p in procs) / n
    avg_wt = sum(p.waiting_time for p in procs) / n
    avg_rt = sum(p.response_time for p in procs) / n
    return rows, {"avg_tat": round(avg_tat, 2), "avg_wt": round(avg_wt, 2), "avg_rt": round(avg_rt, 2)}


CPU_ALGO_KEYS = {
    "fcfs": "FCFS",
    "sjf_np": "SJF (Non-Preemptive)",
    "srtf": "SRTF (SJF Preemptive)",
    "priority_np": "Priority (Non-Preemptive)",
    "priority_p": "Priority (Preemptive)",
    "rr": "Round Robin",
}


def run_cpu_algo(key, procs, quantum=2):
    if key == "rr":
        return cpu.round_robin(procs, quantum=quantum)
    name = CPU_ALGO_KEYS.get(key)
    if name is None or name not in cpu.ALGORITHMS:
        raise ValueError(f"Unknown CPU algorithm: {key}")
    return cpu.ALGORITHMS[name](procs)


# ---------------------------------------------------------------------------
# 1. CPU SCHEDULING
# ---------------------------------------------------------------------------

@app.route("/api/cpu/run", methods=["POST"])
def api_cpu_run():
    data = request.get_json(force=True)
    raw_procs = data.get("processes", [])
    if not raw_procs:
        return error("Provide at least one process.")

    algos = data.get("algorithms", [])
    if not algos:
        return error("Select at least one algorithm.")
    quantum = int(data.get("quantum", 2))
    if quantum < 1:
        return error("Quantum must be at least 1.")

    try:
        procs = [
            cpu.Process(
                pid=p.get("pid") or f"P{i+1}",
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 0)),
            )
            for i, p in enumerate(raw_procs)
        ]
    except (KeyError, ValueError, TypeError) as e:
        return error(f"Invalid process data: {e}")

    if any(p.burst_time <= 0 for p in procs):
        return error("Burst time must be a positive integer.")
    if any(p.arrival_time < 0 for p in procs):
        return error("Arrival time cannot be negative.")

    results = {}
    for key in algos:
        try:
            result_procs, schedule = run_cpu_algo(key, procs, quantum=quantum)
        except ValueError as e:
            return error(str(e))
        rows, avgs = process_table(result_procs)
        label = "Round Robin" if key == "rr" else CPU_ALGO_KEYS[key]
        results[key] = {
            "label": label + (f" (q={quantum})" if key == "rr" else ""),
            "rows": rows,
            "averages": avgs,
            "schedule": [{"pid": pid, "start": s, "end": e} for pid, s, e in schedule],
        }

    return jsonify({"ok": True, "results": results})


# ---------------------------------------------------------------------------
# 2. MEMORY MANAGEMENT
# ---------------------------------------------------------------------------

MEM_STRATEGY_KEYS = {
    "first_fit": "First Fit",
    "best_fit": "Best Fit",
    "worst_fit": "Worst Fit",
}


@app.route("/api/memory/run", methods=["POST"])
def api_memory_run():
    data = request.get_json(force=True)
    total_size = data.get("total_size")
    raw_requests = data.get("requests", [])
    strategies = data.get("strategies", [])
    compaction = bool(data.get("compaction", False))

    if not total_size or int(total_size) <= 0:
        return error("Total memory size must be a positive integer.")
    if not raw_requests:
        return error("Provide at least one allocation request.")
    if not strategies:
        return error("Select at least one strategy.")

    total_size = int(total_size)
    requests = []
    try:
        for r in raw_requests:
            if r["type"] == "alloc":
                requests.append(("alloc", r["pid"], int(r["size"])))
            elif r["type"] == "free":
                requests.append(("free", r["pid"]))
            else:
                return error(f"Unknown request type: {r['type']}")
    except (KeyError, ValueError, TypeError) as e:
        return error(f"Invalid request data: {e}")

    results = {}
    for strat_key in strategies:
        strat_label = MEM_STRATEGY_KEYS.get(strat_key)
        if strat_label is None:
            return error(f"Unknown strategy: {strat_key}")
        mgr, snapshots = mem.run_allocation_sequence(
            total_size, requests, strategy=strat_key, compaction=compaction
        )
        snap_out = []
        for label, blocks in snapshots:
            snap_out.append({
                "label": label,
                "blocks": [
                    {"start": b.start, "size": b.size, "end": b.end, "pid": b.process_id}
                    for b in blocks
                ],
            })
        results[strat_key] = {
            "label": strat_label,
            "log": mgr.log,
            "snapshots": snap_out,
            "final_blocks": snap_out[-1]["blocks"],
            "utilization": round(mgr.utilization(), 2),
            "fragmentation": mgr.fragmentation(),
        }

    return jsonify({"ok": True, "results": results, "total_size": total_size, "compaction": compaction})


# ---------------------------------------------------------------------------
# 3. VIRTUAL MEMORY (Page Replacement)
# ---------------------------------------------------------------------------

VM_ALGO_KEYS = {
    "fifo": "FIFO",
    "lru": "LRU",
    "optimal": "Optimal",
}


@app.route("/api/vm/run", methods=["POST"])
def api_vm_run():
    data = request.get_json(force=True)
    ref_string = data.get("reference_string", "")
    num_frames = data.get("num_frames")
    algos = data.get("algorithms", [])

    if not algos:
        return error("Select at least one algorithm.")
    try:
        reference = [int(x) for x in str(ref_string).replace(",", " ").split()]
    except ValueError:
        return error("Reference string must contain only integers.")
    if not reference:
        return error("Provide a reference string.")
    try:
        num_frames = int(num_frames)
    except (TypeError, ValueError):
        return error("Number of frames must be an integer.")
    if num_frames < 1:
        return error("Number of frames must be at least 1.")

    results = {}
    for key in algos:
        label = VM_ALGO_KEYS.get(key)
        if label is None or label not in vm.ALGORITHMS:
            return error(f"Unknown algorithm: {key}")
        history, faults = vm.ALGORITHMS[label](reference, num_frames)
        hist_out = [{"page": pg, "frames": fr, "fault": fault} for pg, fr, fault in history]
        results[key] = {
            "label": label,
            "history": hist_out,
            "faults": faults,
            "total_refs": len(reference),
            "hit_ratio": round((1 - faults / len(reference)) * 100, 2),
        }

    return jsonify({"ok": True, "results": results, "num_frames": num_frames, "reference": reference})


# ---------------------------------------------------------------------------
# 4. DISK SCHEDULING
# ---------------------------------------------------------------------------

DISK_ALGO_KEYS = {
    "fcfs": "FCFS",
    "sstf": "SSTF",
    "scan": "SCAN",
    "cscan": "C-SCAN",
    "look": "LOOK",
    "clook": "C-LOOK",
}


@app.route("/api/disk/run", methods=["POST"])
def api_disk_run():
    data = request.get_json(force=True)
    raw_requests = data.get("requests", "")
    head = data.get("head")
    disk_size = data.get("disk_size")
    direction = data.get("direction", "right")
    algos = data.get("algorithms", [])

    if not algos:
        return error("Select at least one algorithm.")
    try:
        requests = [int(x) for x in str(raw_requests).replace(",", " ").split()]
    except ValueError:
        return error("Disk requests must contain only integers.")
    if not requests:
        return error("Provide at least one disk request.")
    try:
        head = int(head)
        disk_size = int(disk_size)
    except (TypeError, ValueError):
        return error("Head position and disk size must be integers.")
    if disk_size < 1:
        return error("Disk size must be positive.")
    if head < 0 or head >= disk_size:
        return error(f"Head position must be within [0, {disk_size - 1}].")
    if any(r < 0 or r >= disk_size for r in requests):
        return error(f"All requests must be within [0, {disk_size - 1}].")
    if direction not in ("left", "right"):
        return error("Direction must be 'left' or 'right'.")

    def run(name):
        if name in disk.ALGORITHMS_NO_DIRECTION:
            return disk.ALGORITHMS_NO_DIRECTION[name](requests, head)
        elif name == "SCAN":
            return disk.scan(requests, head, disk_size, direction)
        elif name == "C-SCAN":
            return disk.cscan(requests, head, disk_size, direction)
        elif name == "LOOK":
            return disk.look(requests, head, direction)
        elif name == "C-LOOK":
            return disk.clook(requests, head, direction)

    results = {}
    for key in algos:
        label = DISK_ALGO_KEYS.get(key)
        if label is None:
            return error(f"Unknown algorithm: {key}")
        order, total = run(label)
        results[key] = {"label": label, "order": order, "total_movement": total}

    return jsonify({
        "ok": True, "results": results, "head": head, "disk_size": disk_size, "direction": direction
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
