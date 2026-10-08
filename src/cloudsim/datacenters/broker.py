"""
PyCloudSim Broker Module.

Implements the DatacenterBroker SimEntity that submits VMs and Cloudlets
to Datacenters on behalf of users and collects results.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Optional, TYPE_CHECKING

from cloudsim.core.entity import SimEntity
from cloudsim.core.event import Event
from cloudsim.core.constants import EventType, CloudletState, VMState

if TYPE_CHECKING:
    from cloudsim.vms.vm import VM
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.datacenters.datacenter import Datacenter

logger = logging.getLogger(__name__)


class DatacenterBroker(SimEntity):
    """
    Mediates between users and Datacenters.

    The Broker accepts VM and Cloudlet lists from the user, submits VM
    creation requests to available Datacenters, assigns Cloudlets to VMs
    using the injected scheduler, and collects results.

    Args:
        name:      Human-readable broker name.
        scheduler: A CloudletScheduler instance that maps cloudlets to VMs.
    """

    def __init__(self, name: str, scheduler) -> None:
        super().__init__(name)
        self.scheduler = scheduler
        self._datacenters: List["Datacenter"] = []
        self._vms: List["VM"] = []
        self._cloudlets: List["Cloudlet"] = []
        self._completed_cloudlets: List["Cloudlet"] = []
        self._vm_datacenter_map: Dict[int, "Datacenter"] = {}
        self._vms_created: int = 0
        self._vms_requested: int = 0

    # ------------------------------------------------------------------
    # User-facing API
    # ------------------------------------------------------------------

    def add_datacenter(self, datacenter: "Datacenter") -> None:
        """Register a datacenter with this broker."""
        self._datacenters.append(datacenter)

    def submit_vm_list(self, vms: List["VM"]) -> None:
        """Register VMs to be created when the simulation starts."""
        self._vms.extend(vms)

    def submit_cloudlet_list(self, cloudlets: List["Cloudlet"]) -> None:
        """Register cloudlets to be executed after VMs are ready."""
        self._cloudlets.extend(cloudlets)

    @property
    def completed_cloudlets(self) -> List["Cloudlet"]:
        """Cloudlets that have finished execution."""
        return self._completed_cloudlets

    # ------------------------------------------------------------------
    # SimEntity lifecycle
    # ------------------------------------------------------------------

    def start_entity(self) -> None:
        """On simulation start: request VM creation in the first datacenter."""
        if not self._datacenters:
            logger.error("[%s] No datacenters registered!", self.name)
            return

        self._vms_requested = len(self._vms)
        for vm in self._vms:
            dc = self._select_datacenter(vm)
            if dc:
                self._vm_datacenter_map[vm.vm_id] = dc
                assert self._simulation is not None
                self._simulation.schedule(
                    Event(
                        time=self._simulation.clock.now(),
                        event_type=EventType.VM_CREATE,
                        source=self,
                        destination=dc,
                        data=vm,
                    )
                )

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def process_event(self, event: Event) -> None:
        """Route incoming events to handlers."""
        handlers = {
            "VM_CREATE_ACK": self._handle_vm_create_ack,
            EventType.CLOUDLET_COMPLETE: self._handle_cloudlet_complete,
        }
        handler = handlers.get(event.event_type)
        if handler:
            handler(event)
        else:
            logger.debug("%s ignoring event %r", self.name, event)

    def _handle_vm_create_ack(self, event: Event) -> None:
        """Process VM creation acknowledgement; once all VMs are up, submit cloudlets."""
        payload = event.data
        vm = payload["vm"]
        success = payload["success"]

        if success:
            self._vms_created += 1
            logger.info(
                "[%s] VM %d created (%d/%d).",
                self.name, vm.vm_id, self._vms_created, self._vms_requested,
            )
        else:
            logger.warning("[%s] VM %d creation FAILED.", self.name, vm.vm_id)

        if self._vms_created == self._vms_requested:
            self._submit_cloudlets()

    def _submit_cloudlets(self) -> None:
        """Use the scheduler to assign cloudlets to VMs, then submit each to its datacenter."""
        running_vms = [vm for vm in self._vms if vm.state == VMState.RUNNING]
        self.scheduler.submit_cloudlets(self._cloudlets, running_vms)

        for cloudlet in self._cloudlets:
            if cloudlet.assigned_vm_id < 0:
                logger.warning(
                    "[%s] Cloudlet %d was not assigned to any VM.", self.name, cloudlet.cloudlet_id
                )
                continue

            dc = self._vm_datacenter_map.get(cloudlet.assigned_vm_id)
            if dc is None:
                logger.error(
                    "[%s] No datacenter for VM %d.", self.name, cloudlet.assigned_vm_id
                )
                continue

            assert self._simulation is not None
            submit_at = max(self._simulation.clock.now(), cloudlet.arrival_time)
            cloudlet.submit_time = submit_at
            self._simulation.schedule(
                Event(
                    time=submit_at,
                    event_type=EventType.CLOUDLET_SUBMIT,
                    source=self,
                    destination=dc,
                    data=cloudlet,
                )
            )

    def _handle_cloudlet_complete(self, event: Event) -> None:
        """Mark a cloudlet as finished and dispatch the next queued cloudlet."""
        cloudlet: "Cloudlet" = event.data
        assert self._simulation is not None
        cloudlet.finish_time = self._simulation.clock.now()
        cloudlet.state = CloudletState.SUCCESS
        self._completed_cloudlets.append(cloudlet)
        logger.info(
            "[%s] Cloudlet %d completed at %.4f (exec=%.4fs, wait=%.4fs).",
            self.name,
            cloudlet.cloudlet_id,
            cloudlet.finish_time,
            cloudlet.execution_time,
            cloudlet.waiting_time,
        )

        dc = self._vm_datacenter_map.get(cloudlet.assigned_vm_id)
        if dc is not None:
            dc.on_cloudlet_finished(cloudlet, self)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _select_datacenter(self, vm: "VM") -> Optional["Datacenter"]:
        """Select the first available datacenter (simple policy)."""
        return self._datacenters[0] if self._datacenters else None
