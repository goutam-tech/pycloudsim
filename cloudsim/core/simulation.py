# """
# PyCloudSim Simulation Engine.

# Orchestrates the discrete-event simulation loop, manages entity registration,
# and drives the global clock forward by processing events in chronological order.
# """

# from __future__ import annotations
# import logging
# from typing import Dict, List, Optional

# from cloudsim.core.clock import SimulationClock
# from cloudsim.core.entity import SimEntity
# from cloudsim.core.event import Event
# from cloudsim.core.event_queue import EventQueue
# from cloudsim.core.constants import EventType

# logger = logging.getLogger(__name__)


# class Simulation:
#     """
#     Core discrete-event simulation engine.

#     Manages the lifecycle of all simulation entities, the global event queue,
#     and the simulation clock. Entities register with the simulation, receive
#     events, and schedule future events through the engine.

#     Example:
#         >>> sim = Simulation()
#         >>> sim.add_entity(datacenter)
#         >>> sim.add_entity(broker)
#         >>> sim.run()
#         >>> print(sim.clock.now())
#     """

#     def __init__(self, termination_time: float = float("inf")) -> None:
#         """
#         Initialize the simulation.

#         Args:
#             termination_time: Maximum simulation time. Defaults to infinity
#                               (simulation ends when the event queue is empty).
#         """
#         self.clock: SimulationClock = SimulationClock()
#         self._event_queue: EventQueue = EventQueue()
#         self._entities: Dict[int, SimEntity] = {}
#         self._next_entity_id: int = 0
#         self.termination_time: float = termination_time
#         self._running: bool = False
#         self._total_events_processed: int = 0

#     # ------------------------------------------------------------------
#     # Entity management
#     # ------------------------------------------------------------------

#     def add_entity(self, entity: SimEntity) -> int:
#         """
#         Register an entity with the simulation.

#         Args:
#             entity: The SimEntity to register.

#         Returns:
#             The unique integer ID assigned to the entity.
#         """
#         entity_id = self._next_entity_id
#         self._next_entity_id += 1
#         entity.entity_id = entity_id
#         entity.set_simulation(self)
#         self._entities[entity_id] = entity
#         logger.debug("Registered entity %r with id=%d", entity.name, entity_id)
#         return entity_id

#     def get_entity(self, entity_id: int) -> Optional[SimEntity]:
#         """
#         Retrieve a registered entity by ID.

#         Args:
#             entity_id: The integer ID of the entity.

#         Returns:
#             The entity, or None if not found.
#         """
#         return self._entities.get(entity_id)

#     def get_entities(self) -> List[SimEntity]:
#         """Return a list of all registered entities."""
#         return list(self._entities.values())

#     # ------------------------------------------------------------------
#     # Event scheduling
#     # ------------------------------------------------------------------

#     def schedule(self, event: Event) -> None:
#         """
#         Schedule an event for future processing.

#         Args:
#             event: The Event to schedule. Its time must be >= current clock time.
#         """
#         if event.time < self.clock.now():
#             logger.warning(
#                 "Scheduling event %r in the past (now=%.4f). Clamping to now.",
#                 event,
#                 self.clock.now(),
#             )
#             event.time = self.clock.now()
#         self._event_queue.push(event)

#     def schedule_now(
#         self,
#         event_type: str,
#         source: Optional[SimEntity],
#         destination: Optional[SimEntity],
#         data: Optional[object] = None,
#     ) -> None:
#         """
#         Convenience method: schedule an event at the current simulation time.

#         Args:
#             event_type: The event type string.
#             source: The entity sending the event.
#             destination: The entity receiving the event.
#             data: Optional payload.
#         """
#         self.schedule(
#             Event(
#                 time=self.clock.now(),
#                 event_type=event_type,
#                 source=source,
#                 destination=destination,
#                 data=data,
#             )
#         )

#     # ------------------------------------------------------------------
#     # Simulation loop
#     # ------------------------------------------------------------------

#     def run(self) -> None:
#         """
#         Start the simulation and process all events.

#         Calls ``start_entity()`` on all registered entities, then enters the
#         main event loop. The loop ends when the event queue is empty or the
#         clock reaches ``termination_time``.
#         """
#         logger.info("Simulation starting. Entities: %d", len(self._entities))
#         self._running = True

#         # Notify all entities the simulation has started
#         for entity in self._entities.values():
#             entity.start_entity()

#         # Main event loop
#         while not self._event_queue.is_empty():
#             event = self._event_queue.pop()

#             if event.time > self.termination_time:
#                 logger.info(
#                     "Termination time %.4f reached. Stopping.", self.termination_time
#                 )
#                 break

#             self.clock.advance(event.time)
#             self._total_events_processed += 1
#             logger.debug("Processing %r", event)

#             if event.destination is not None:
#                 event.destination.process_event(event)
#             else:
#                 logger.warning("Event %r has no destination; dropping.", event)

#         # Shutdown phase
#         for entity in self._entities.values():
#             entity.shutdown_entity()

#         self._running = False
#         logger.info(
#             "Simulation finished at time=%.4f. Events processed: %d",
#             self.clock.now(),
#             self._total_events_processed,
#         )

#     def is_running(self) -> bool:
#         """Return True if the simulation loop is currently active."""
#         return self._running

#     @property
#     def total_events_processed(self) -> int:
#         """Total number of events processed during the last run."""
#         return self._total_events_processed

#     def __repr__(self) -> str:
#         return (
#             f"Simulation(entities={len(self._entities)}, "
#             f"clock={self.clock.now():.4f}, "
#             f"events_processed={self._total_events_processed})"
#         )

"""
PyCloudSim Simulation Engine.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from cloudsim.core.clock import SimulationClock
from cloudsim.core.entity import SimEntity
from cloudsim.core.event import Event
from cloudsim.core.event_queue import EventQueue

from cloudsim.metrics.utilization import UtilizationCollector

logger = logging.getLogger(__name__)


class Simulation:
    """
    Core discrete-event simulation engine.
    """

    def __init__(
        self,
        termination_time: float = float("inf")
    ) -> None:

        self.clock: SimulationClock = SimulationClock()

        self._event_queue: EventQueue = EventQueue()

        self._entities: Dict[int, SimEntity] = {}

        self._next_entity_id: int = 0

        self.termination_time: float = termination_time

        self._running: bool = False

        self._total_events_processed: int = 0

        # ---------------------------------------------
        # Utilization tracking
        # ---------------------------------------------

        self.utilization_collector = UtilizationCollector()

    # ---------------------------------------------------------
    # Entity management
    # ---------------------------------------------------------

    def add_entity(
        self,
        entity: SimEntity
    ) -> int:

        entity_id = self._next_entity_id

        self._next_entity_id += 1

        entity.entity_id = entity_id

        entity.set_simulation(self)

        self._entities[entity_id] = entity

        logger.debug(
            "Registered entity %r with id=%d",
            entity.name,
            entity_id
        )

        return entity_id

    def get_entity(
        self,
        entity_id: int
    ) -> Optional[SimEntity]:

        return self._entities.get(entity_id)

    def get_entities(self) -> List[SimEntity]:

        return list(
            self._entities.values()
        )

    # ---------------------------------------------------------
    # Event scheduling
    # ---------------------------------------------------------

    def schedule(
        self,
        event: Event
    ) -> None:

        if event.time < self.clock.now():

            logger.warning(
                "Scheduling event %r in the past "
                "(now=%.4f). Clamping to now.",
                event,
                self.clock.now()
            )

            event.time = self.clock.now()

        self._event_queue.push(event)

    def schedule_now(
        self,
        event_type: str,
        source: Optional[SimEntity],
        destination: Optional[SimEntity],
        data: Optional[object] = None,
    ) -> None:

        self.schedule(
            Event(
                time=self.clock.now(),
                event_type=event_type,
                source=source,
                destination=destination,
                data=data,
            )
        )

    # ---------------------------------------------------------
    # Utilization tracking
    # ---------------------------------------------------------

    def _record_utilization_snapshots(self) -> None:

        current_time = self.clock.now()

        for entity in self._entities.values():

            if not hasattr(entity, "hosts"):
                continue

            for host in entity.hosts:

                try:

                    host.record_utilization_sample()

                    self.utilization_collector.record_host_snapshot(
                        current_time,
                        host
                    )

                except Exception as exc:

                    logger.debug(
                        "Host snapshot failed: %s",
                        exc
                    )

                for vm in host.vms:

                    try:

                        vm.record_utilization_sample()

                        self.utilization_collector.record_vm_snapshot(
                            current_time,
                            vm
                        )

                    except Exception as exc:

                        logger.debug(
                            "VM snapshot failed: %s",
                            exc
                        )
        

    # ---------------------------------------------------------
    # Simulation loop
    # ---------------------------------------------------------

    def run(self) -> None:

        logger.info(
            "Simulation starting. Entities: %d",
            len(self._entities)
        )

        self._running = True

        # ---------------------------------------------
        # Startup phase
        # ---------------------------------------------

        for entity in self._entities.values():
            entity.start_entity()

        # Initial utilization snapshot

        self._record_utilization_snapshots()

        # ---------------------------------------------
        # Main event loop
        # ---------------------------------------------

        while not self._event_queue.is_empty():

            event = self._event_queue.pop()

            if event.time > self.termination_time:

                logger.info(
                    "Termination time %.4f reached. "
                    "Stopping.",
                    self.termination_time
                )

                break

            self.clock.advance(
                event.time
            )

            self._total_events_processed += 1

            logger.debug(
                "Processing %r",
                event
            )

            if event.destination is not None:

                event.destination.process_event(
                    event
                )

                # Record utilization after every event

                self._record_utilization_snapshots()

            else:

                logger.warning(
                    "Event %r has no destination; "
                    "dropping.",
                    event
                )

        # Final snapshot

        self._record_utilization_snapshots()

        # ---------------------------------------------
        # Shutdown phase
        # ---------------------------------------------

        for entity in self._entities.values():
            entity.shutdown_entity()

        self._running = False

        logger.info(
            "Simulation finished at time=%.4f. "
            "Events processed: %d",
            self.clock.now(),
            self._total_events_processed
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def hosts(self):

        hosts = []

        for entity in self._entities.values():

            if hasattr(entity, "hosts"):

                hosts.extend(
                    entity.hosts
                )

        return hosts

    @property
    def vms(self):

        vms = []

        for host in self.hosts:

            vms.extend(
                host.vms
            )

        return vms

    @property
    def utilization_metrics(self):

        return self.utilization_collector

    def is_running(self) -> bool:

        return self._running

    @property
    def total_events_processed(self) -> int:

        return self._total_events_processed

    def __repr__(self) -> str:

        return (
            f"Simulation("
            f"entities={len(self._entities)}, "
            f"clock={self.clock.now():.4f}, "
            f"events_processed="
            f"{self._total_events_processed})"
        )