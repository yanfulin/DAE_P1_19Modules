
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar, Iterable
from collections import deque

T = TypeVar("T")

class RingBuffer(Generic[T]):
    """
    Fixed-size ring buffer. Stores latest N items.
    """
    def __init__(self, maxlen: int):
        self._dq = deque(maxlen=maxlen)

    def append(self, item: T) -> None:
        self._dq.append(item)

    def snapshot(self) -> List[T]:
        return list(self._dq)

    def last(self) -> Optional[T]:
        return self._dq[-1] if self._dq else None

    def __len__(self) -> int:
        return len(self._dq)
