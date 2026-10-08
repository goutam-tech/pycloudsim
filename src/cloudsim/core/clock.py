"""
PyCloudSim Clock Module.

Maintains the global simulation clock for discrete-event simulation.
"""

from __future__ import annotations


class SimulationClock:
    """
    Global simulation clock.

    Tracks the current simulation time and provides methods to advance
    the clock as events are processed.

    Example:
        >>> clock = SimulationClock()
        >>> clock.advance(5.0)
        >>> clock.now()
        5.0
    """

    def __init__(self) -> None:
        """Initialize the clock at time zero."""
        self._time: float = 0.0

    def now(self) -> float:
        """Return the current simulation time."""
        return self._time

    def advance(self, time: float) -> None:
        """
        Advance the clock to the given time.

        Args:
            time: New simulation time. Must not be less than current time.

        Raises:
            ValueError: If time is in the past.
        """
        if time < self._time:
            raise ValueError(
                f"Cannot move clock backwards: current={self._time}, requested={time}"
            )
        self._time = time

    def reset(self) -> None:
        """Reset the clock to time zero."""
        self._time = 0.0

    def __repr__(self) -> str:
        return f"SimulationClock(time={self._time:.4f})"
