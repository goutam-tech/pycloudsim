"""
PyCloudSim Entity Module.

Defines the abstract base class for all simulation entities.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cloudsim.core.simulation import Simulation
    from cloudsim.core.event import Event


class SimEntity(ABC):
    """
    Abstract base class for all simulation entities.

    Every participant in the simulation (Datacenter, Broker, Host, etc.)
    extends this class to receive and handle events.

    Attributes:
        name: Human-readable identifier for this entity.
        entity_id: Unique integer ID assigned by the simulation.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize a simulation entity.

        Args:
            name: Human-readable name for this entity.
        """
        self.name: str = name
        self.entity_id: int = -1
        self._simulation: "Simulation | None" = None

    def set_simulation(self, simulation: "Simulation") -> None:
        """
        Bind this entity to a running simulation.

        Args:
            simulation: The simulation instance managing this entity.
        """
        self._simulation = simulation

    @abstractmethod
    def process_event(self, event: "Event") -> None:
        """
        Handle an incoming simulation event.

        Args:
            event: The event to process.
        """
        ...

    def start_entity(self) -> None:
        """Called when the simulation starts. Override to send initial events."""
        pass

    def shutdown_entity(self) -> None:
        """Called when the simulation ends. Override for cleanup logic."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.entity_id}, name={self.name!r})"
