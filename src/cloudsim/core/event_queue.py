"""
PyCloudSim Event Queue Module.

Implements a priority queue for simulation events using Python's heapq.
"""

from __future__ import annotations
import heapq
from typing import List, Optional

from cloudsim.core.event import Event


class EventQueue:
    """
    Priority queue for simulation events.

    Events are dequeued in chronological order. When two events share
    the same time, the event with the lower priority integer value is
    processed first.

    Example:
        >>> queue = EventQueue()
        >>> queue.push(Event(time=1.0, event_type="VM_CREATE"))
        >>> event = queue.pop()
    """

    def __init__(self) -> None:
        """Initialize an empty event queue."""
        self._heap: List[Event] = []

    def push(self, event: Event) -> None:
        """
        Add an event to the queue.

        Args:
            event: The Event to schedule.
        """
        heapq.heappush(self._heap, event)

    def pop(self) -> Event:
        """
        Remove and return the earliest event.

        Returns:
            The event with the smallest time (and priority on ties).

        Raises:
            IndexError: If the queue is empty.
        """
        return heapq.heappop(self._heap)

    def peek(self) -> Optional[Event]:
        """
        Return the earliest event without removing it.

        Returns:
            The earliest event, or None if the queue is empty.
        """
        return self._heap[0] if self._heap else None

    def is_empty(self) -> bool:
        """Return True if the queue contains no events."""
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def __repr__(self) -> str:
        return f"EventQueue(size={len(self._heap)})"
