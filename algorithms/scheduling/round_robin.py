"""
Round Robin Cloudlet Scheduler.

Distributes cloudlets evenly across available VMs using modulo arithmetic.
This algorithm is suitable as a baseline for comparison with more
sophisticated scheduling strategies.
"""

from __future__ import annotations
from typing import List, Optional

from cloudsim.schedulers.schedulers import CloudletScheduler
from cloudsim.core.constants import CloudletState

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


class RoundRobinScheduler(CloudletScheduler):
    """
    Round Robin cloudlet-to-VM scheduler.

    Assigns cloudlets to VMs in a circular, sequential fashion using
    modulo arithmetic. Each cloudlet is dispatched to:

        vm = vms[index % len(vms)]

    This achieves uniform distribution when cloudlet workloads are homogeneous.
    The scheduler is stateless between ``submit_cloudlets`` calls, making it
    easy to extend with priority tiers or weighted round robin.

    Example:
        >>> scheduler = RoundRobinScheduler()
        >>> scheduler.submit_cloudlets(cloudlets, vms)
        >>> scheduler.is_finished()
        False
    """

    def __init__(self) -> None:
        """Initialize the Round Robin scheduler."""
        self._cloudlets: List["Cloudlet"] = []
        self._assignment_index: int = 0

    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        """
        Assign each cloudlet to a VM using round robin ordering.

        The assignment counter is global across multiple ``submit_cloudlets``
        calls so that successive batches continue the circular sequence.

        Args:
            cloudlets: Cloudlets waiting to be scheduled.
            vms:       Available VMs (must be non-empty).

        Raises:
            ValueError: If *vms* is empty.
        """
        if not vms:
            raise ValueError("RoundRobinScheduler requires at least one VM.")

        for cloudlet in cloudlets:
            vm = vms[self._assignment_index % len(vms)]
            cloudlet.assigned_vm_id = vm.vm_id
            cloudlet.state = CloudletState.QUEUED
            vm.cloudlets.append(cloudlet)
            self._cloudlets.append(cloudlet)
            self._assignment_index += 1

    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        """Return the next queued or in-execution cloudlet."""
        for cl in self._cloudlets:
            if cl.state in (CloudletState.QUEUED, CloudletState.INEXEC):
                return cl
        return None

    def is_finished(self) -> bool:
        """Return True when every submitted cloudlet has completed."""
        return all(cl.state == CloudletState.SUCCESS for cl in self._cloudlets)

    def reset(self) -> None:
        """Reset scheduler state for reuse in a new simulation run."""
        self._cloudlets.clear()
        self._assignment_index = 0
