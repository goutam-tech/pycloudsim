"""
PyCloudSim Schedulers Module.

Defines abstract base schedulers and built-in Time-Shared and Space-Shared
scheduling policies for Cloudlets and VMs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


class CloudletScheduler(ABC):
    """Abstract base class for cloudlet-to-VM scheduling policies."""

    @abstractmethod
    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        ...

    @abstractmethod
    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        ...

    @abstractmethod
    def is_finished(self) -> bool:
        ...


class VMScheduler(ABC):
    """Abstract base class for VM scheduling policies on a host."""

    @abstractmethod
    def allocate_pes_for_vm(self, vm: "VM", mips_share: List[float]) -> bool:
        ...

    @abstractmethod
    def deallocate_pes_for_vm(self, vm: "VM") -> None:
        ...


class TimeSharedScheduler(CloudletScheduler):
    """Time-shared policy: concurrent cloudlets on a VM split MIPS evenly."""

    def __init__(self) -> None:
        self._cloudlets: List["Cloudlet"] = []
        self._vm_cloudlet_map: Dict[int, List["Cloudlet"]] = {}

    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        from cloudsim.core.constants import CloudletState

        if not vms:
            return

        for idx, cloudlet in enumerate(cloudlets):
            vm = vms[idx % len(vms)]
            cloudlet.assigned_vm_id = vm.vm_id
            cloudlet.state = CloudletState.INEXEC
            self._cloudlets.append(cloudlet)
            self._vm_cloudlet_map.setdefault(vm.vm_id, []).append(cloudlet)
            vm.cloudlets.append(cloudlet)
            vm.assign_cloudlet(cloudlet)

        self._update_vm_shares(vms)

    def _update_vm_shares(self, vms: List["VM"]) -> None:
        for vm in vms:
            running = self._vm_cloudlet_map.get(vm.vm_id, [])
            if not running:
                vm.used_mips = 0.0
                continue

            share = vm.total_mips / len(running)
            for cloudlet in running:
                cloudlet.current_mips = share
            vm.update_used_mips()

    def complete_cloudlet(self, cloudlet: "Cloudlet", vms: List["VM"]) -> None:
        from cloudsim.core.constants import CloudletState

        cloudlet.state = CloudletState.SUCCESS
        vm = next((v for v in vms if v.vm_id == cloudlet.assigned_vm_id), None)
        if vm is None:
            return

        vm.complete_cloudlet(cloudlet)
        running = self._vm_cloudlet_map.get(vm.vm_id, [])
        if cloudlet in running:
            running.remove(cloudlet)
        self._update_vm_shares(vms)

    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        from cloudsim.core.constants import CloudletState

        for cloudlet in self._cloudlets:
            if cloudlet.state == CloudletState.INEXEC:
                return cloudlet
        return None

    def estimate_finish_time(self, cloudlet: "Cloudlet", vm: "VM") -> float:
        concurrent = max(1, len(self._vm_cloudlet_map.get(vm.vm_id, [cloudlet])))
        effective_mips = vm.total_mips / concurrent
        return cloudlet.arrival_time + cloudlet.length / effective_mips

    def is_finished(self) -> bool:
        from cloudsim.core.constants import CloudletState

        return all(cl.state == CloudletState.SUCCESS for cl in self._cloudlets)


class SpaceSharedScheduler(CloudletScheduler):
    """Space-shared policy: one cloudlet per VM at a time with a waiting queue."""

    def __init__(self) -> None:
        self._waiting_queue: Deque["Cloudlet"] = deque()
        self._running: List["Cloudlet"] = []
        self._completed: List["Cloudlet"] = []
        self._vm_busy: Dict[int, bool] = {}

    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        from cloudsim.core.constants import CloudletState

        for vm in vms:
            self._vm_busy.setdefault(vm.vm_id, False)

        for cloudlet in cloudlets:
            cloudlet.state = CloudletState.QUEUED
            self._waiting_queue.append(cloudlet)

        for vm in vms:
            if not self._vm_busy[vm.vm_id] and self._waiting_queue:
                cloudlet = self._waiting_queue.popleft()
                cloudlet.assigned_vm_id = vm.vm_id
                cloudlet.state = CloudletState.INEXEC
                cloudlet.current_mips = vm.total_mips
                vm.assign_cloudlet(cloudlet)
                vm.update_used_mips()
                self._running.append(cloudlet)
                self._vm_busy[vm.vm_id] = True
                vm.cloudlets.append(cloudlet)

    def complete_cloudlet(self, cloudlet: "Cloudlet", vms: List["VM"]) -> None:
        from cloudsim.core.constants import CloudletState

        cloudlet.state = CloudletState.SUCCESS
        if cloudlet in self._running:
            self._running.remove(cloudlet)
        self._completed.append(cloudlet)

        vm = next((v for v in vms if v.vm_id == cloudlet.assigned_vm_id), None)
        if vm is None:
            return

        vm.complete_cloudlet(cloudlet)
        vm.update_used_mips()
        self._vm_busy[vm.vm_id] = False

        if self._waiting_queue:
            next_cloudlet = self._waiting_queue.popleft()
            next_cloudlet.assigned_vm_id = vm.vm_id
            next_cloudlet.state = CloudletState.INEXEC
            next_cloudlet.current_mips = vm.total_mips
            vm.assign_cloudlet(next_cloudlet)
            vm.update_used_mips()
            self._running.append(next_cloudlet)
            self._vm_busy[vm.vm_id] = True
            vm.cloudlets.append(next_cloudlet)

    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        return self._running[0] if self._running else None

    def is_finished(self) -> bool:
        return not self._waiting_queue and not self._running
