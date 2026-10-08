"""
PyCloudSim Event Module.

Defines the Event dataclass used in discrete-event simulation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(order=True)
class Event:
    """
    Represents a simulation event in the discrete-event simulation engine.

    Events are ordered by time, then by priority (lower value = higher priority).

    Attributes:
        time: Simulation time at which the event should be processed.
        event_type: String identifier for the event type.
        source: Entity that generated the event.
        destination: Entity that should handle the event.
        data: Optional payload associated with the event.
        priority: Tie-breaking priority (lower = higher priority).
    """

    time: float
    priority: int = field(default=0, compare=True)
    event_type: str = field(default="", compare=False)
    source: Optional[Any] = field(default=None, compare=False)
    destination: Optional[Any] = field(default=None, compare=False)
    data: Optional[Any] = field(default=None, compare=False)

    def __repr__(self) -> str:
        return (
            f"Event(time={self.time:.4f}, type={self.event_type}, "
            f"src={getattr(self.source, 'name', self.source)}, "
            f"dst={getattr(self.destination, 'name', self.destination)})"
        )
