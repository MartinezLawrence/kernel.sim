"""
disk_scheduling.py
===================

Implements:
  - FCFS
  - SSTF      (Shortest Seek Time First)
  - SCAN      (elevator algorithm, travels to disk end)
  - C-SCAN    (circular SCAN)
  - LOOK      (like SCAN but turns around at the last request, not disk end)
  - C-LOOK    (circular LOOK)

Every algorithm returns:
  (order, total_movement)
    order           -> list[int] cylinder visiting order, starting with the head position
    total_movement  -> int, total number of cylinders the head travels
"""

from typing import List, Tuple


def _total_movement(order: List[int]) -> int:
    return sum(abs(order[i + 1] - order[i]) for i in range(len(order) - 1))


def _dedupe_consecutive(order: List[int]) -> List[int]:
    cleaned = [order[0]]
    for x in order[1:]:
        if x != cleaned[-1]:
            cleaned.append(x)
    return cleaned


def fcfs(requests: List[int], head: int) -> Tuple[List[int], int]:
    order = [head] + list(requests)
    return order, _total_movement(order)


def sstf(requests: List[int], head: int) -> Tuple[List[int], int]:
    reqs = list(requests)
    order = [head]
    current = head
    while reqs:
        nxt = min(reqs, key=lambda r: abs(r - current))
        order.append(nxt)
        reqs.remove(nxt)
        current = nxt
    return order, _total_movement(order)


def scan(requests: List[int], head: int, disk_size: int, direction: str = "right") -> Tuple[List[int], int]:
    reqs = sorted(set(requests))
    order = [head]
    if direction == "right":
        right = [r for r in reqs if r >= head]
        left = [r for r in reqs if r < head]
        order += right
        order.append(disk_size - 1)
        order += sorted(left, reverse=True)
    else:
        left = [r for r in reqs if r <= head]
        right = [r for r in reqs if r > head]
        order += sorted(left, reverse=True)
        order.append(0)
        order += right
    order = _dedupe_consecutive(order)
    return order, _total_movement(order)


def cscan(requests: List[int], head: int, disk_size: int, direction: str = "right") -> Tuple[List[int], int]:
    reqs = sorted(set(requests))
    order = [head]
    if direction == "right":
        right = [r for r in reqs if r >= head]
        left = [r for r in reqs if r < head]
        order += right
        order.append(disk_size - 1)
        order.append(0)
        order += sorted(left)
    else:
        left = [r for r in reqs if r <= head]
        right = [r for r in reqs if r > head]
        order += sorted(left, reverse=True)
        order.append(0)
        order.append(disk_size - 1)
        order += sorted(right, reverse=True)
    order = _dedupe_consecutive(order)
    return order, _total_movement(order)


def look(requests: List[int], head: int, direction: str = "right") -> Tuple[List[int], int]:
    reqs = sorted(set(requests))
    order = [head]
    if direction == "right":
        right = [r for r in reqs if r >= head]
        left = [r for r in reqs if r < head]
        order += right
        order += sorted(left, reverse=True)
    else:
        left = [r for r in reqs if r <= head]
        right = [r for r in reqs if r > head]
        order += sorted(left, reverse=True)
        order += right
    order = _dedupe_consecutive(order)
    return order, _total_movement(order)


def clook(requests: List[int], head: int, direction: str = "right") -> Tuple[List[int], int]:
    reqs = sorted(set(requests))
    order = [head]
    if direction == "right":
        right = [r for r in reqs if r >= head]
        left = [r for r in reqs if r < head]
        order += right
        order += sorted(left)
    else:
        left = [r for r in reqs if r <= head]
        right = [r for r in reqs if r > head]
        order += sorted(left, reverse=True)
        order += sorted(right, reverse=True)
    order = _dedupe_consecutive(order)
    return order, _total_movement(order)


ALGORITHMS_NO_DIRECTION = {
    "FCFS": fcfs,
    "SSTF": sstf,
}

ALGORITHMS_WITH_DIRECTION = {
    "SCAN": scan,
    "C-SCAN": cscan,
    "LOOK": look,
    "C-LOOK": clook,
}
