"""
PyCloudSim Cloudlet Module.

Represents a user task submitted to the cloud for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cloudsim.core.constants import CloudletState


@dataclass
class Cloudlet:
    """A unit of work submitted by a user for execution on a VM."""

    cloudlet_id: int
    length: float
    pes: int = 1
    file_size: float = 300.0
    output_size: float = 300.0
    arrival_time: float = 0.0
    priority: int = 0
    deadline: Optional[float] = None

    ram_required: int = 512
    storage_required: int = 100
    bandwidth_required: int = 100

    state: str = field(default=CloudletState.CREATED, init=False, repr=False)
    assigned_vm_id: int = field(default=-1, init=False, repr=False)
    assigned_host_id: int = field(default=-1, init=False, repr=False)

    submit_time: float = field(default=0.0, init=False, repr=False)
    start_time: float = field(default=0.0, init=False, repr=False)
    finish_time: float = field(default=0.0, init=False, repr=False)
    actual_cpu_time: float = field(default=0.0, init=False, repr=False)
    current_mips: float = field(default=0.0, init=False, repr=False)

    def _reference_time(self) -> float:
        """Time from which waiting and response are measured."""
        return self.submit_time if self.submit_time > 0 else self.arrival_time

    @property
    def execution_time(self) -> float:
        """Wall-clock execution time (finish - start)."""
        return max(0.0, self.finish_time - self.start_time)

    @property
    def waiting_time(self) -> float:
        """Time spent waiting after submission before execution began."""
        return max(0.0, self.start_time - self._reference_time())

    @property
    def response_time(self) -> float:
        """Total time from submission to completion."""
        return max(0.0, self.finish_time - self._reference_time())

    @property
    def is_finished(self) -> bool:
        return self.state == CloudletState.SUCCESS

    @property
    def sla_violated(self) -> bool:
        if self.deadline is None:
            return False
        return self.finish_time > self.deadline

    def __hash__(self) -> int:
        return hash(self.cloudlet_id)
