"""
Min-Min Cloudlet Scheduler.

Assigns cloudlets using the Min-Min scheduling algorithm.
For every unscheduled cloudlet, the scheduler finds the VM
that gives the minimum completion time. Among those minimum
completion times, the cloudlet with the overall smallest value
is scheduled first.

This algorithm generally minimizes average completion time
and performs well when cloudlet lengths vary.
"""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from cloudsim.schedulers.schedulers import CloudletScheduler
from cloudsim.core.constants import CloudletState

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


class MinMinScheduler(CloudletScheduler):
    """
    Min-Min cloudlet-to-VM scheduler.

    For every unscheduled cloudlet:

        completion_time = vm_ready_time + (cloudlet.length / vm.mips)

    The scheduler first finds the VM with the minimum completion
    time for each cloudlet.

    It then selects the cloudlet having the smallest completion
    time among all candidates and assigns it to its best VM.

    This process repeats until every cloudlet has been scheduled.

    Example:
        >>> scheduler = MinMinScheduler()
        >>> scheduler.submit_cloudlets(cloudlets, vms)
        >>> scheduler.is_finished()
        False
    """

    def __init__(self) -> None:
        """Initialize the Min-Min scheduler."""
        self._cloudlets: List["Cloudlet"] = []

    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        """
        Assign cloudlets using the Min-Min scheduling algorithm.

        Args:
            cloudlets: Cloudlets waiting to be scheduled.
            vms: Available virtual machines.

        Raises:
            ValueError: If no VMs are available.
        """
        if not vms:
            raise ValueError("MinMinScheduler requires at least one VM.")

        # Ready time of each VM
        vm_ready_time = {vm.vm_id: 0.0 for vm in vms}

        unscheduled = list(cloudlets)

        while unscheduled:

            best_cloudlet = None
            best_vm = None
            best_completion = float("inf")

            # Find the minimum completion time for every cloudlet
            for cloudlet in unscheduled:

                min_vm = None
                min_completion = float("inf")

                for vm in vms:
                    execution_time = cloudlet.length / vm.mips
                    completion_time = vm_ready_time[vm.vm_id] + execution_time

                    if completion_time < min_completion:
                        min_completion = completion_time
                        min_vm = vm

                # Select the cloudlet having overall minimum completion time
                if min_completion < best_completion:
                    best_completion = min_completion
                    best_cloudlet = cloudlet
                    best_vm = min_vm

            # Assign selected cloudlet
            best_cloudlet.assigned_vm_id = best_vm.vm_id
            best_cloudlet.state = CloudletState.QUEUED

            best_vm.cloudlets.append(best_cloudlet)
            self._cloudlets.append(best_cloudlet)

            # Update VM availability
            vm_ready_time[best_vm.vm_id] = best_completion

            unscheduled.remove(best_cloudlet)

    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        """Return the next queued or executing cloudlet."""
        for cl in self._cloudlets:
            if cl.state in (CloudletState.QUEUED, CloudletState.INEXEC):
                return cl
        return None

    def is_finished(self) -> bool:
        """Return True when all submitted cloudlets have completed."""
        return all(cl.state == CloudletState.SUCCESS for cl in self._cloudlets)

    def reset(self) -> None:
        """Reset scheduler state for reuse."""
        self._cloudlets.clear()