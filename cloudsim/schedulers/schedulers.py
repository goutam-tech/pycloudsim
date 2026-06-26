"""
PyCloudSim Schedulers Module.

Defines abstract base schedulers and built-in Time-Shared and Space-Shared
scheduling policies for Cloudlets and VMs.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


# ---------------------------------------------------------------------------
# Abstract base classes
# ---------------------------------------------------------------------------


class CloudletScheduler(ABC):
    """
    Abstract base class for cloudlet scheduling policies.

    A CloudletScheduler determines how cloudlets are assigned to VMs and
    tracks their progress during execution.
    """

    @abstractmethod
    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        """
        Submit a batch of cloudlets for scheduling across the given VMs.

        Args:
            cloudlets: Cloudlets waiting to be scheduled.
            vms: Available VMs to schedule onto.
        """
        ...

    @abstractmethod
    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        """Return the next cloudlet to execute, or None if the queue is empty."""
        ...

    @abstractmethod
    def is_finished(self) -> bool:
        """Return True when all submitted cloudlets have been completed."""
        ...


class VMScheduler(ABC):
    """
    Abstract base class for VM scheduling policies on a Host.

    A VMScheduler determines how MIPS from a Host's PEs are distributed
    among the VMs currently running on that Host.
    """

    @abstractmethod
    def allocate_pes_for_vm(self, vm: "VM", mips_share: List[float]) -> bool:
        """
        Allocate PE MIPS to a VM.

        Args:
            vm:         The VM requesting PE allocation.
            mips_share: A list of MIPS values, one per PE.

        Returns:
            True if allocation succeeded.
        """
        ...

    @abstractmethod
    def deallocate_pes_for_vm(self, vm: "VM") -> None:
        """Release PE allocations for a VM."""
        ...


# ---------------------------------------------------------------------------
# Time-Shared Scheduler
# ---------------------------------------------------------------------------

class TimeSharedScheduler(CloudletScheduler):

    def __init__(self) -> None:

        self._cloudlets = []

        self._vm_cloudlet_map = {}

    def submit_cloudlets(self, cloudlets, vms) -> None:

        from cloudsim.core.constants import CloudletState

        if not vms:
            return

        for idx, cloudlet in enumerate(cloudlets):

            vm = vms[idx % len(vms)]

            cloudlet.assigned_vm_id = vm.vm_id

            cloudlet.state = CloudletState.INEXEC

            self._cloudlets.append(cloudlet)

            self._vm_cloudlet_map.setdefault(
                vm.vm_id,
                []
            ).append(cloudlet)

            vm.cloudlets.append(cloudlet)

            vm.assign_cloudlet(cloudlet)

        self._update_vm_shares(vms)

    def _update_vm_shares(self, vms):

        for vm in vms:

            running = self._vm_cloudlet_map.get(
                vm.vm_id,
                []
            )

            if not running:
                vm.used_mips = 0.0
                continue

            share = vm.total_mips / len(running)

            for cl in running:

                cl.current_mips = share

            vm.update_used_mips()

    def complete_cloudlet(
        self,
        cloudlet,
        vms
    ):

        from cloudsim.core.constants import CloudletState

        cloudlet.state = CloudletState.SUCCESS

        vm = next(
            (
                v
                for v in vms
                if v.vm_id == cloudlet.assigned_vm_id
            ),
            None
        )

        if vm:

            vm.complete_cloudlet(
                cloudlet
            )

            lst = self._vm_cloudlet_map.get(
                vm.vm_id,
                []
            )

            if cloudlet in lst:
                lst.remove(cloudlet)

            self._update_vm_shares(vms)

    def get_next_cloudlet(self):

        from cloudsim.core.constants import CloudletState

        for cl in self._cloudlets:

            if cl.state == CloudletState.INEXEC:
                return cl

        return None

    def estimate_finish_time(
        self,
        cloudlet,
        vm
    ):

        concurrent = max(
            1,
            len(
                self._vm_cloudlet_map.get(
                    vm.vm_id,
                    [cloudlet]
                )
            )
        )

        effective_mips = (
            vm.total_mips
            / concurrent
        )

        return (
            cloudlet.arrival_time
            + cloudlet.length
            / effective_mips
        )

    def is_finished(self):

        from cloudsim.core.constants import CloudletState

        return all(
            cl.state == CloudletState.SUCCESS
            for cl in self._cloudlets
        )


# ---------------------------------------------------------------------------
# Space-Shared Scheduler
# ---------------------------------------------------------------------------


# class SpaceSharedScheduler(CloudletScheduler):
#     """
#     Space-shared (FCFS) cloudlet scheduling policy.

#     Each VM executes one cloudlet at a time. Cloudlets waiting for a free VM
#     are held in a queue. When a VM finishes its current cloudlet the next
#     queued cloudlet is dispatched to it.

#     Example:
#         >>> scheduler = SpaceSharedScheduler()
#         >>> scheduler.submit_cloudlets(cloudlets, vms)
#     """

#     def __init__(self) -> None:
#         from collections import deque
#         self._waiting_queue: "deque[Cloudlet]" = __import__("collections").deque()
#         self._running: List["Cloudlet"] = []
#         self._completed: List["Cloudlet"] = []
#         self._vm_busy: Dict[int, bool] = {}

#     def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
#         """Enqueue cloudlets and greedily dispatch to free VMs."""
#         from cloudsim.core.constants import CloudletState

#         for vm in vms:
#             self._vm_busy.setdefault(vm.vm_id, False)

#         for cloudlet in cloudlets:
#             cloudlet.state = CloudletState.QUEUED
#             self._waiting_queue.append(cloudlet)

#         # Immediately dispatch to free VMs
#         for vm in vms:
#             if not self._vm_busy[vm.vm_id] and self._waiting_queue:
#                 cloudlet = self._waiting_queue.popleft()
#                 cloudlet.assigned_vm_id = vm.vm_id
#                 cloudlet.state = CloudletState.INEXEC
#                 self._running.append(cloudlet)
#                 self._vm_busy[vm.vm_id] = True
#                 vm.cloudlets.append(cloudlet)

#     def complete_cloudlet(self, cloudlet: "Cloudlet", vms: List["VM"]) -> None:
#         """
#         Mark a cloudlet as complete and dispatch the next queued cloudlet.

#         Args:
#             cloudlet: The cloudlet that just finished.
#             vms: Available VMs (used to find the now-free VM).
#         """
#         from cloudsim.core.constants import CloudletState

#         cloudlet.state = CloudletState.SUCCESS
#         self._running.remove(cloudlet)
#         self._completed.append(cloudlet)
#         self._vm_busy[cloudlet.assigned_vm_id] = False

#         if self._waiting_queue:
#             # Re-dispatch to the freed VM
#             vm = next((v for v in vms if v.vm_id == cloudlet.assigned_vm_id), None)
#             if vm:
#                 next_cl = self._waiting_queue.popleft()
#                 next_cl.assigned_vm_id = vm.vm_id
#                 next_cl.state = CloudletState.INEXEC
#                 self._running.append(next_cl)
#                 self._vm_busy[vm.vm_id] = True
#                 vm.cloudlets.append(next_cl)

#     def get_next_cloudlet(self) -> Optional["Cloudlet"]:
#         """Return the first running cloudlet or None."""
#         return self._running[0] if self._running else None

#     def is_finished(self) -> bool:
#         """Return True when all queued and running cloudlets have completed."""
#         from cloudsim.core.constants import CloudletState

#         return (
#             not self._waiting_queue
#             and not self._running
#         )

class SpaceSharedScheduler(CloudletScheduler):

    def __init__(self):

        from collections import deque

        self._waiting_queue = deque()

        self._running = []

        self._completed = []

        self._vm_busy = {}

    def submit_cloudlets(
        self,
        cloudlets,
        vms
    ):

        from cloudsim.core.constants import CloudletState

        for vm in vms:
            self._vm_busy.setdefault(
                vm.vm_id,
                False
            )

        for cl in cloudlets:

            cl.state = CloudletState.QUEUED

            self._waiting_queue.append(cl)

        for vm in vms:

            if (
                not self._vm_busy[vm.vm_id]
                and self._waiting_queue
            ):

                cl = self._waiting_queue.popleft()

                cl.assigned_vm_id = vm.vm_id

                cl.state = CloudletState.INEXEC

                cl.current_mips = vm.total_mips

                vm.assign_cloudlet(cl)

                vm.update_used_mips()

                self._running.append(cl)

                self._vm_busy[vm.vm_id] = True

                vm.cloudlets.append(cl)

    def complete_cloudlet(
        self,
        cloudlet,
        vms
    ):

        from cloudsim.core.constants import CloudletState

        cloudlet.state = CloudletState.SUCCESS

        if cloudlet in self._running:
            self._running.remove(
                cloudlet
            )

        self._completed.append(
            cloudlet
        )

        vm = next(
            (
                v
                for v in vms
                if v.vm_id
                == cloudlet.assigned_vm_id
            ),
            None
        )

        if vm:

            vm.complete_cloudlet(
                cloudlet
            )

            vm.update_used_mips()

            self._vm_busy[
                vm.vm_id
            ] = False

            if self._waiting_queue:

                next_cl = (
                    self._waiting_queue
                    .popleft()
                )

                next_cl.assigned_vm_id = (
                    vm.vm_id
                )

                next_cl.state = (
                    CloudletState.INEXEC
                )

                next_cl.current_mips = (
                    vm.total_mips
                )

                vm.assign_cloudlet(
                    next_cl
                )

                vm.update_used_mips()

                self._running.append(
                    next_cl
                )

                self._vm_busy[
                    vm.vm_id
                ] = True

                vm.cloudlets.append(
                    next_cl
                )

    def get_next_cloudlet(self):

        return (
            self._running[0]
            if self._running
            else None
        )

    def is_finished(self):

        return (
            not self._waiting_queue
            and not self._running
        )