"""
PyCloudSim Simulation Engine.

Orchestrates the discrete-event simulation loop and drives the global clock.
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
    """Core discrete-event simulation engine."""

    def __init__(self, termination_time: float = float("inf")) -> None:
        self.clock: SimulationClock = SimulationClock()
        self._event_queue: EventQueue = EventQueue()
        self._entities: Dict[int, SimEntity] = {}
        self._next_entity_id: int = 0
        self.termination_time: float = termination_time
        self._running: bool = False
        self._total_events_processed: int = 0
        self.utilization_collector = UtilizationCollector()

    def add_entity(self, entity: SimEntity) -> int:
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        entity.entity_id = entity_id
        entity.set_simulation(self)
        self._entities[entity_id] = entity
        logger.debug("Registered entity %r with id=%d", entity.name, entity_id)
        return entity_id

    def get_entity(self, entity_id: int) -> Optional[SimEntity]:
        return self._entities.get(entity_id)

    def get_entities(self) -> List[SimEntity]:
        return list(self._entities.values())

    def schedule(self, event: Event) -> None:
        if event.time < self.clock.now():
            logger.warning(
                "Scheduling event %r in the past (now=%.4f). Clamping to now.",
                event,
                self.clock.now(),
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

    def _record_utilization_snapshots(self) -> None:
        current_time = self.clock.now()
        for entity in self._entities.values():
            if not hasattr(entity, "hosts"):
                continue
            for host in entity.hosts:
                try:
                    host.record_utilization_sample()
                    self.utilization_collector.record_host_snapshot(current_time, host)
                except Exception as exc:
                    logger.debug("Host snapshot failed: %s", exc)

                for vm in host.vms:
                    try:
                        vm.record_utilization_sample()
                        self.utilization_collector.record_vm_snapshot(current_time, vm)
                    except Exception as exc:
                        logger.debug("VM snapshot failed: %s", exc)

    def run(self) -> None:
        logger.info("Simulation starting. Entities: %d", len(self._entities))
        self._running = True

        for entity in self._entities.values():
            entity.start_entity()

        self._record_utilization_snapshots()

        while not self._event_queue.is_empty():
            event = self._event_queue.pop()

            if event.time > self.termination_time:
                logger.info("Termination time %.4f reached. Stopping.", self.termination_time)
                break

            self.clock.advance(event.time)
            self._total_events_processed += 1
            logger.debug("Processing %r", event)

            if event.destination is not None:
                event.destination.process_event(event)
                self._record_utilization_snapshots()
            else:
                logger.warning("Event %r has no destination; dropping.", event)

        self._record_utilization_snapshots()

        for entity in self._entities.values():
            entity.shutdown_entity()

        self._running = False
        logger.info(
            "Simulation finished at time=%.4f. Events processed: %d",
            self.clock.now(),
            self._total_events_processed,
        )

    @property
    def hosts(self):
        hosts = []
        for entity in self._entities.values():
            if hasattr(entity, "hosts"):
                hosts.extend(entity.hosts)
        return hosts

    @property
    def vms(self):
        vms = []
        for host in self.hosts:
            vms.extend(host.vms)
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
            f"Simulation(entities={len(self._entities)}, "
            f"clock={self.clock.now():.4f}, "
            f"events_processed={self._total_events_processed})"
        )
