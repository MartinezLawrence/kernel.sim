"""
virtual_memory.py
==================
Page replacement algorithms.

Implements:
  - FIFO     (First In First Out)
  - LRU      (Least Recently Used)
  - Optimal  (Belady's optimal / clairvoyant algorithm)

Every algorithm returns:
  (history, faults)
    history -> list[(page, frame_state_at_this_step, was_fault: bool)]
    faults  -> total number of page faults
"""

from collections import deque
from typing import List, Tuple


def fifo(reference_string: List[int], num_frames: int):
    frames: List[int] = []
    queue: deque = deque()
    history = []
    faults = 0

    for page in reference_string:
        fault = False
        if page not in frames:
            fault = True
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
                queue.append(page)
            else:
                evict = queue.popleft()
                idx = frames.index(evict)
                frames[idx] = page
                queue.append(page)
        history.append((page, list(frames), fault))

    return history, faults


def lru(reference_string: List[int], num_frames: int):
    frames: List[int] = []
    recent: List[int] = []  # most-recently-used at the end
    history = []
    faults = 0

    for page in reference_string:
        fault = False
        if page in frames:
            recent.remove(page)
            recent.append(page)
        else:
            fault = True
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
            else:
                lru_page = recent.pop(0)
                idx = frames.index(lru_page)
                frames[idx] = page
            recent.append(page)
        history.append((page, list(frames), fault))

    return history, faults


def optimal(reference_string: List[int], num_frames: int):
    frames: List[int] = []
    history = []
    faults = 0
    n = len(reference_string)

    for i, page in enumerate(reference_string):
        fault = False
        if page not in frames:
            fault = True
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
            else:
                future = reference_string[i + 1:]
                farthest = -1
                evict_idx = 0
                for fi, fp in enumerate(frames):
                    if fp not in future:
                        evict_idx = fi
                        break
                    else:
                        next_use = future.index(fp)
                        if next_use > farthest:
                            farthest = next_use
                            evict_idx = fi
                frames[evict_idx] = page
        history.append((page, list(frames), fault))

    return history, faults


ALGORITHMS = {
    "FIFO": fifo,
    "LRU": lru,
    "Optimal": optimal,
}
