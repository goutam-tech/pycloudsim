"""
PyCloudSim Datacenter Module.

Implements the Datacenter SimEntity that manages Hosts, allocates VMs,
and executes Cloudlets on behalf of a Broker.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Optional, TYPE_CHECKING

from cloudsim.core.entity import SimEntity
from cloudsim.core.event import Event
from cloudsim.core.constants import EventType, VMState, CloudletState
from cloudsim.datacenters.characteristics import DatacenterCharacteristics

if TYPE_CHECKING:
    from cloudsim.hosts.host import Host
    from cloudsim.vms.vm import VM
    from cloudsim.cloudlets.cloudlet import Cloudlet

logger = logging.getLogger(__name__)


class Datacenter(SimEntity):
    """
    Cloud datacenter that manages a set of hosts and executes VM/cloudlet requests.

    The Datacenter receives events from the Broker, allocates VMs to Hosts using
    a First Fit strategy, executes Cloudlets on the allocated VMs, and sends
    completion events back to the Broker.

    Args:
        name:            Human-readable name.
        hosts:           List of Host objects available in this datacenter.
        characteristics: Pricing and SLA metadata.
        scheduling_interval: Simulation time step between scheduling cycles.
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

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def process_event(self, event: Event) -> None:
        """Route incoming events to the appropriate handler."""
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
        """Allocate a VM to the most suitable host (First Fit)."""
        vm: "VM" = event.data
        allocated = False
        for host in self.hosts:
            if host.is_suitable_for_vm(vm):
                success = host.allocate_resources_for_vm(vm)
                if success:
                    self._vm_table[vm.vm_id] = vm
                    allocated = True
                    logger.info(
                        "[%s] VM %d allocated on Host %d",
                        self.name, vm.vm_id, host.host_id,
                    )
                    break

        if not allocated:
            logger.warning("[%s] Could not allocate VM %d – insufficient resources.", self.name, vm.vm_id)

        # Notify broker
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
        """Execute a cloudlet on its assigned VM and schedule the completion event."""
        cloudlet: "Cloudlet" = event.data
        vm = self._vm_table.get(cloudlet.assigned_vm_id)

        if vm is None:
            logger.error(
                "[%s] Cloudlet %d references unknown VM %d",
                self.name, cloudlet.cloudlet_id, cloudlet.assigned_vm_id,
            )
            return

        now = self._simulation.clock.now() if self._simulation else 0.0
        cloudlet.start_time = now
        cloudlet.state = CloudletState.INEXEC
        cloudlet.current_mips = vm.total_mips
        vm.assign_cloudlet(cloudlet)
        vm.update_used_mips()
        self._cloudlet_table[cloudlet.cloudlet_id] = cloudlet

        # Estimate completion time: length (MI) / MIPS
        # exec_time = cloudlet.length / max(vm.mips, 1.0)
        exec_time = (
            cloudlet.length
            / max(cloudlet.current_mips, 1.0)
        )
        finish_time = now + exec_time
        cloudlet.actual_cpu_time = exec_time

        logger.info(
            "[%s] Cloudlet %d → VM %d | start=%.4f finish=%.4f",
            self.name, cloudlet.cloudlet_id, vm.vm_id, now, finish_time,
        )

        if self._simulation and event.source:
            self._simulation.schedule(
                Event(
                    time=finish_time,
                    event_type=EventType.CLOUDLET_COMPLETE,
                    source=self,
                    destination=event.source,
                    data=cloudlet,
                )
            )

    def _handle_simulation_end(self, event: Event) -> None:
        """Handle simulation shutdown."""
        logger.info("[%s] Received simulation end signal.", self.name)

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    def total_energy(self, duration: float) -> float:
        """
        Estimate total energy consumption across all hosts (Wh).

        Args:
            duration: Simulation duration in seconds.

        Returns:
            Energy in Watt-hours.
        """
        from cloudsim.hosts.host import PowerHost

        total_joules = 0.0
        for host in self.hosts:
            if isinstance(host, PowerHost):
                power = host.current_power()
            else:
                power = 200.0  # Default assumption
            total_joules += power * duration
        return total_joules / 3600.0  # Convert to Wh

    def vm_count(self) -> int:
        """Return the number of currently allocated VMs."""
        return len(self._vm_table)
