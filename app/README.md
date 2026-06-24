# kernel.sim — Operating Systems Concepts Console

A Flask web app we made that simulates four core OS subsystems and renders every
result as an interactive, in-browser visualization (no static PNGs, no
matplotlib popups). Built with a dark, instrument-panel visual style meant to
read like a systems-monitoring console.

**Modules**
1. **CPU Scheduling** — FCFS, SJF (Non-Preemptive), SRTF, Priority
   (Non-Preemptive), Priority (Preemptive), Round Robin
2. **Memory Management** — First Fit, Best Fit, Worst Fit, each runnable
   **with or without compaction**
3. **Virtual Memory** — FIFO, LRU, Optimal (Belady's) page replacement
4. **Disk Scheduling** — FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK

You can select **any combination of algorithms** per module and run them
side by side — the app shows per-algorithm metrics plus an automatic
comparison bar chart whenever 2+ algorithms are selected.

---

## 1. Project structure

```
app/
├── app.py                   Flask app + JSON REST API (all 4 modules)
├── cpu_scheduling.py        CPU scheduling algorithms (pure Python, no Flask)
├── memory_management.py     Contiguous memory allocation + compaction
├── virtual_memory.py        Page replacement algorithms
├── disk_scheduling.py       Disk head scheduling algorithms
├── requirements.txt
├── templates/
│   └── index.html           Single-page app shell
└── static/
    ├── css/style.css        Design system (tokens, layout, components)
    └── js/
        ├── app.js           Shared utilities: trace renderer, bar chart, data table
        ├── cpu.js            CPU module: editable process table + run + render
        ├── memory.js         Memory module: editable request sequence + run + render
        ├── vm.js             Virtual memory module: run + render
        └── disk.js           Disk module: run + render (SVG seek-path chart)
```

The four algorithm modules (`cpu_scheduling.py`, `memory_management.py`,
`virtual_memory.py`, `disk_scheduling.py`) are plain Python with **no Flask
or web dependency** — they can be imported and unit-tested on their own, or
reused in a CLI tool.

---

## 2. Setup

**Requirements:** Visual Studio with Python 3.9+

You can simply run this by running app.py in VSTUDIO and ctrl + left click the localhost.

---

## 3. How to use each module

### CPU Scheduling
1. Edit the process table (PID, Arrival Time, Burst Time, Priority). Add or
   remove rows with **+ Add process** / the **✕** button.
2. Set the **Time Quantum** if you plan to run Round Robin.
3. Tick one or more algorithm chips.
4. Click **Run Simulation**.
5. Each selected algorithm renders as a Gantt-style trace, a metrics table
   (CT / TAT / WT / RT), and average WT/TAT/RT pills. With 2+ algorithms
   selected, a comparison bar chart appears at the bottom.

### Memory Management
1. Set **Total Memory Size**.
2. Toggle **Compaction** on/off — this changes allocator behavior whenever a
   request can't be satisfied by any single free block but enough free space
   exists in total.
3. Build the allocation sequence: each row is either `alloc <pid> <size>` or
   `free <pid>`, processed top to bottom.
4. Tick one or more strategies (First / Best / Worst Fit).
5. Click **Run Simulation** to see: a "final memory layout" strip, a full
   step-by-step timeline (one strip per request), an allocation log
   (failures shown in red, compaction events in amber), and utilization /
   external-fragmentation metrics.

> **Tip — seeing compaction in action:** allocate several same-size blocks,
> free two non-adjacent ones, then request something larger than any single
> free gap but smaller than the combined free space. With compaction off
> you'll see a red `FAILED to allocate...` log line; with compaction on,
> you'll see `** Compaction performed **` followed by a successful
> allocation.

### Virtual Memory (Page Replacement)
1. Enter a **Page Reference String** (space or comma separated).
2. Set **Number of Frames**.
3. Tick one or more algorithms (FIFO / LRU / Optimal).
4. Click **Run Simulation** to see a frame-occupancy grid per algorithm —
   each column is one reference, each row is a frame slot, faults are
   highlighted red and hits green, with a Page Faults / Hit Ratio summary
   and comparison chart.

### Disk Scheduling
1. Enter the **Request Queue** (cylinder numbers).
2. Set **Initial Head Position** and **Disk Size**.
3. Choose **Scan Direction** (used by SCAN / C-SCAN / LOOK / C-LOOK).
4. Tick one or more algorithms.
5. Click **Run Simulation** to see an SVG seek-path chart (head position vs.
   step), the full visiting order, total head movement, and a comparison
   chart across algorithms.

---
