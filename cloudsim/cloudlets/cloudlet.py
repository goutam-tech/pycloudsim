# """
# PyCloudSim Cloudlet Module.

# Defines the Cloudlet entity, which represents a user task (job) submitted
# to the cloud for execution.
# """

# from __future__ import annotations
# from dataclasses import dataclass, field
# from typing import Optional

# from cloudsim.core.constants import CloudletState


# @dataclass
# class Cloudlet:
#     """
#     A Cloudlet represents a unit of work submitted by a user.

#     Analogous to a job or task in traditional HPC scheduling. The simulation
#     assigns each cloudlet to a VM, tracks its execution, and records timing.

#     Attributes:
#         cloudlet_id:  Unique identifier.
#         length:       Computational length in Million Instructions (MI).
#         pes:          Number of PEs (cores) required.
#         file_size:    Input data size in bytes.
#         output_size:  Output data size in bytes.
#         arrival_time: Time at which the cloudlet is submitted.
#         priority:     Scheduling priority (lower integer = higher priority).
#         deadline:     Optional deadline in simulation time units.
#     """

#     cloudlet_id: int
#     length: float
#     pes: int = 1
#     file_size: float = 300.0
#     output_size: float = 300.0
#     arrival_time: float = 0.0
#     priority: int = 0
#     deadline: Optional[float] = None

#     # Runtime state
#     state: str = field(default=CloudletState.CREATED, init=False, repr=False)
#     assigned_vm_id: int = field(default=-1, init=False, repr=False)
#     assigned_host_id: int = field(default=-1, init=False, repr=False)

#     # Timing
#     start_time: float = field(default=0.0, init=False, repr=False)
#     finish_time: float = field(default=0.0, init=False, repr=False)
#     actual_cpu_time: float = field(default=0.0, init=False, repr=False)

#     @property
#     def execution_time(self) -> float:
#         """Wall-clock execution time (finish - start)."""
#         return max(0.0, self.finish_time - self.start_time)

#     @property
#     def waiting_time(self) -> float:
#         """Time spent waiting before execution began (start - arrival)."""
#         return max(0.0, self.start_time - self.arrival_time)

#     @property
#     def response_time(self) -> float:
#         """Total response time from arrival to completion."""
#         return max(0.0, self.finish_time - self.arrival_time)

#     @property
#     def is_finished(self) -> bool:
#         """Return True if the cloudlet has completed successfully."""
#         return self.state == CloudletState.SUCCESS

#     @property
#     def sla_violated(self) -> bool:
#         """Return True if the cloudlet missed its deadline."""
#         if self.deadline is None:
#             return False
#         return self.finish_time > self.deadline

#     def __hash__(self) -> int:
#         return hash(self.cloudlet_id)


"""
PyCloudSim Cloudlet Module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from cloudsim.core.constants import CloudletState


@dataclass
class Cloudlet:
    """
    Cloudlet (Task)
    """

    cloudlet_id: int
    length: float

    pes: int = 1

    file_size: float = 300.0
    output_size: float = 300.0

    arrival_time: float = 0.0
    priority: int = 0
    deadline: Optional[float] = None

    # -------------------------------------------------
    # Resource requirements
    # -------------------------------------------------

    ram_required: int = 512
    storage_required: int = 100
    bandwidth_required: int = 100

    # -------------------------------------------------
    # Runtime state
    # -------------------------------------------------

    state: str = field(
        default=CloudletState.CREATED,
        init=False,
        repr=False
    )

    assigned_vm_id: int = field(
        default=-1,
        init=False,
        repr=False
    )

    assigned_host_id: int = field(
        default=-1,
        init=False,
        repr=False
    )

    # -------------------------------------------------
    # Execution tracking
    # -------------------------------------------------

    start_time: float = field(
        default=0.0,
        init=False,
        repr=False
    )

    finish_time: float = field(
        default=0.0,
        init=False,
        repr=False
    )

    actual_cpu_time: float = field(
        default=0.0,
        init=False,
        repr=False
    )

    current_mips: float = field(
        default=0.0,
        init=False,
        repr=False
    )

    # -------------------------------------------------
    # Metrics
    # -------------------------------------------------

    @property
    def execution_time(self) -> float:
        return max(
            0.0,
            self.finish_time - self.start_time
        )

    @property
    def waiting_time(self) -> float:
        return max(
            0.0,
            self.start_time - self.arrival_time
        )

    @property
    def response_time(self) -> float:
        return max(
            0.0,
            self.finish_time - self.arrival_time
        )

    @property
    def is_finished(self) -> bool:
        return (
            self.state
            == CloudletState.SUCCESS
        )

    @property
    def sla_violated(self) -> bool:

        if self.deadline is None:
            return False

        return (
            self.finish_time
            > self.deadline
        )

    def __hash__(self) -> int:
        return hash(self.cloudlet_id)