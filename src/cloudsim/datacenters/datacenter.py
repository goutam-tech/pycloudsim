"""
PyCloudSim Datacenter Module.

Implements the Datacenter SimEntity that manages Hosts, allocates VMs,
and executes Cloudlets on behalf of a Broker.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Deque, Dict, List, Optional, TYPE_CHECKING

from cloudsim.core.entity import SimEntity
from cloudsim.core.event import Event
from cloudsim.core.constants import EventType, CloudletState
from cloudsim.datacenters.characteristics import DatacenterCharacteristics

if TYPE_CHECKING:
    from cloudsim.hosts.host import Host
    from cloudsim.vms.vm import VM
    from cloudsim.cloudlets.cloudlet import Cloudlet

logger = logging.getLogger(__name__)


class Datacenter(SimEntity):
    """
    Cloud datacenter that manages hosts, allocates VMs, and executes cloudlets.

    Uses space-shared execution: each VM runs one cloudlet at a time. Cloudlets
    assigned to a busy VM are queued until the VM becomes free.
    """

    def __init__(
        self,
        name: str,
        hosts: List["Host"],
        characteristics: Optional[DatacenterCharacteristics] = None,
        scheduling_interval: float = 0.1,
    ) -> None:
        super().__init__(name)
        self.hosts: List["Host"] = hosts
        self.characteristics: DatacenterCharacteristics = (
            characteristics or DatacenterCharacteristics()
        )
        self.scheduling_interval: float = scheduling_interval
        self._vm_table: Dict[int, "VM"] = {}
        self._cloudlet_table: Dict[int, "Cloudlet"] = {}
        self._vm_queues: Dict[int, Deque["Cloudlet"]] = {}
        self._vm_busy: Dict[int, bool] = {}

    def process_event(self, event: Event) -> None:
        handlers = {
            EventType.VM_CREATE: self._handle_vm_create,
            EventType.CLOUDLET_SUBMIT: self._handle_cloudlet_submit,
            EventType.SIMULATION_END: self._handle_simulation_end,
        }
        handler = handlers.get(event.event_type)
        if handler:
            handler(event)
        else:
            logger.debug("%s ignoring unknown event %r", self.name, event)

    def _handle_vm_create(self, event: Event) -> None:
        vm: "VM" = event.data
        allocated = False
        for host in self.hosts:
            if host.is_suitable_for_vm(vm):
                success = host.allocate_resources_for_vm(vm)
                if success:
                    self._vm_table[vm.vm_id] = vm
                    self._vm_queues.setdefault(vm.vm_id, deque())
                    self._vm_busy.setdefault(vm.vm_id, False)
                    allocated = True
                    logger.info(
                        "[%s] VM %d allocated on Host %d",
                        self.name, vm.vm_id, host.host_id,
                    )
                    break

        if not allocated:
            logger.warning(
                "[%s] Could not allocate VM %d – insufficient resources.",
                self.name, vm.vm_id,
            )

        if self._simulation and event.source:
            self._simulation.schedule(
                Event(
                    time=self._simulation.clock.now(),
                    event_type="VM_CREATE_ACK",
                    source=self,
                    destination=event.source,
                    data={"vm": vm, "success": allocated},
                )
            )

    def _handle_cloudlet_submit(self, event: Event) -> None:
        cloudlet: "Cloudlet" = event.data
        vm = self._vm_table.get(cloudlet.assigned_vm_id)

        if vm is None:
            logger.error(
                "[%s] Cloudlet %d references unknown VM %d",
                self.name, cloudlet.cloudlet_id, cloudlet.assigned_vm_id,
            )
            return

        broker = event.source
        self._vm_queues.setdefault(vm.vm_id, deque())
        self._vm_busy.setdefault(vm.vm_id, False)

        if self._vm_busy[vm.vm_id]:
            cloudlet.state = CloudletState.QUEUED
            self._vm_queues[vm.vm_id].append(cloudlet)
            logger.info(
                "[%s] Cloudlet %d queued on VM %d (queue size=%d)",
                self.name, cloudlet.cloudlet_id, vm.vm_id,
                len(self._vm_queues[vm.vm_id]),
            )
            return

        self._start_cloudlet(cloudlet, vm, broker)

    def _start_cloudlet(
        self,
        cloudlet: "Cloudlet",
        vm: "VM",
        broker: SimEntity,
    ) -> None:
        assert self._simulation is not None

        now = self._simulation.clock.now()
        cloudlet.start_time = now
        cloudlet.state = CloudletState.INEXEC
        cloudlet.current_mips = vm.total_mips
        self._vm_busy[vm.vm_id] = True
        vm.assign_cloudlet(cloudlet)
        self._cloudlet_table[cloudlet.cloudlet_id] = cloudlet

        exec_time = cloudlet.length / max(cloudlet.current_mips, 1.0)
        finish_time = now + exec_time
        cloudlet.actual_cpu_time = exec_time

        logger.info(
            "[%s] Cloudlet %d → VM %d | submit=%.4f start=%.4f finish=%.4f wait=%.4fs",
            self.name,
            cloudlet.cloudlet_id,
            vm.vm_id,
            cloudlet.submit_time,
            now,
            finish_time,
            cloudlet.waiting_time,
        )

        self._simulation.schedule(
            Event(
                time=finish_time,
                event_type=EventType.CLOUDLET_COMPLETE,
                source=self,
                destination=broker,
                data=cloudlet,
            )
        )

    def on_cloudlet_finished(self, cloudlet: "Cloudlet", broker: SimEntity) -> None:
        """Release VM resources and start the next queued cloudlet, if any."""
        vm = self._vm_table.get(cloudlet.assigned_vm_id)
        if vm is None:
            return

        vm.complete_cloudlet(cloudlet)
        self._vm_busy[vm.vm_id] = False

        queue = self._vm_queues.get(vm.vm_id)
        if queue:
            next_cloudlet = queue.popleft()
            self._start_cloudlet(next_cloudlet, vm, broker)

    def _handle_simulation_end(self, event: Event) -> None:
        logger.info("[%s] Received simulation end signal.", self.name)

    def total_energy(self, duration: float) -> float:
        from cloudsim.hosts.host import PowerHost

        total_joules = 0.0
        for host in self.hosts:
            if isinstance(host, PowerHost):
                power = host.current_power()
            else:
                power = 200.0
            total_joules += power * duration
        return total_joules / 3600.0

    def vm_count(self) -> int:
        return len(self._vm_table)
