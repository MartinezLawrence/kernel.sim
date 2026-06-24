"""
memory_management.py
=====================

Implements:
  - First Fit
  - Best Fit
  - Worst Fit
Each strategy can run WITH or WITHOUT compaction.

Compaction: when no free block is large enough for a request, all allocated
blocks are pushed together (defragmented) into one contiguous region, leaving
a single free block at the end -- then allocation is retried.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Block:
    start: int
    size: int
    process_id: Optional[str] = None  # None = free block

    @property
    def end(self):
        return self.start + self.size


class MemoryManager:
    def __init__(self, total_size: int):
        self.total_size = total_size
        self.blocks: List[Block] = [Block(0, total_size, None)]
        self.log: List[str] = []

    def _free_candidates(self, size):
        return [(i, b) for i, b in enumerate(self.blocks) if b.process_id is None and b.size >= size]

    def allocate(self, process_id: str, size: int, strategy: str = "first_fit", compaction: bool = False) -> bool:
        candidates = self._free_candidates(size)

        if not candidates and compaction:
            self.compact()
            candidates = self._free_candidates(size)

        if not candidates:
            self.log.append(f"FAILED to allocate {size} units to {process_id} "
                             f"(no block big enough, strategy={strategy})")
            return False

        if strategy == "first_fit":
            idx, block = candidates[0]
        elif strategy == "best_fit":
            idx, block = min(candidates, key=lambda x: x[1].size)
        elif strategy == "worst_fit":
            idx, block = max(candidates, key=lambda x: x[1].size)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        if block.size == size:
            block.process_id = process_id
        else:
            allocated = Block(block.start, size, process_id)
            remaining = Block(block.start + size, block.size - size, None)
            self.blocks[idx:idx + 1] = [allocated, remaining]

        self.log.append(f"Allocated {size} units to {process_id} at address {block.start} ({strategy})")
        return True

    def deallocate(self, process_id: str) -> bool:
        found = False
        for b in self.blocks:
            if b.process_id == process_id:
                b.process_id = None
                found = True
        if found:
            self._merge_free_blocks()
            self.log.append(f"Deallocated {process_id}")
        else:
            self.log.append(f"Process {process_id} not found (nothing to free)")
        return found

    def _merge_free_blocks(self):
        merged: List[Block] = []
        for b in sorted(self.blocks, key=lambda x: x.start):
            if merged and merged[-1].process_id is None and b.process_id is None:
                merged[-1].size += b.size
            else:
                merged.append(Block(b.start, b.size, b.process_id))
        self.blocks = merged

    def compact(self):
        new_blocks: List[Block] = []
        pos = 0
        for b in sorted(self.blocks, key=lambda x: x.start):
            if b.process_id is not None:
                new_blocks.append(Block(pos, b.size, b.process_id))
                pos += b.size
        free_size = self.total_size - pos
        if free_size > 0:
            new_blocks.append(Block(pos, free_size, None))
        self.blocks = new_blocks
        self.log.append("** Compaction performed **")

    def utilization(self) -> float:
        used = sum(b.size for b in self.blocks if b.process_id)
        return used / self.total_size * 100

    def fragmentation(self) -> int:
        """Total free memory scattered in blocks smaller than the largest free block
        (a simple external-fragmentation indicator)."""
        free_blocks = [b.size for b in self.blocks if b.process_id is None]
        if not free_blocks:
            return 0
        return sum(free_blocks) - max(free_blocks)

    def snapshot(self) -> List[Block]:
        return [Block(b.start, b.size, b.process_id) for b in self.blocks]


def run_allocation_sequence(
    total_size: int,
    requests: List[Tuple],
    strategy: str = "first_fit",
    compaction: bool = False,
):
    """
    requests: list of ('alloc', pid, size) or ('free', pid) tuples, processed in order.

    Returns (manager, snapshots) where snapshots is a list of
    (label, list[Block]) taken after every step -- ready for visualization.
    """
    mgr = MemoryManager(total_size)
    snapshots = [("Initial", mgr.snapshot())]
    for req in requests:
        if req[0] == "alloc":
            _, pid, size = req
            mgr.allocate(pid, size, strategy=strategy, compaction=compaction)
            snapshots.append((f"After alloc {pid}({size})", mgr.snapshot()))
        elif req[0] == "free":
            _, pid = req
            mgr.deallocate(pid)
            snapshots.append((f"After free {pid}", mgr.snapshot()))
        else:
            raise ValueError(f"Unknown request type: {req[0]}")
    return mgr, snapshots


STRATEGIES = {
    "First Fit": "first_fit",
    "Best Fit": "best_fit",
    "Worst Fit": "worst_fit",
}
