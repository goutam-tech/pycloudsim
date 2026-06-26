# """
# PyCloudSim VM Module.

# Defines the VirtualMachine entity representing a guest OS running on a Host.
# """

# from __future__ import annotations
# from dataclasses import dataclass, field
# from typing import List, Optional, TYPE_CHECKING

# from cloudsim.core.constants import VMState

# if TYPE_CHECKING:
#     from cloudsim.cloudlets.cloudlet import Cloudlet
#     from cloudsim.hosts.host import Host


# @dataclass
# class VM:
#     """
#     Virtual Machine entity.

#     Represents a VM guest with defined compute, memory, network, and
#     storage resources. A VM is placed on a Host by the VMAllocationPolicy.

#     Attributes:
#         vm_id:     Unique VM identifier.
#         mips:      Million Instructions Per Second per PE.
#         pes:       Number of Processing Elements (vCPUs).
#         ram:       RAM in MB.
#         bandwidth: Network bandwidth in Mbps.
#         storage:   Disk storage in MB.
#         broker_id: ID of the broker that owns this VM.
#     """

#     vm_id: int
#     mips: float
#     pes: int
#     ram: float
#     bandwidth: float
#     storage: float
#     broker_id: int = -1

#     # Runtime state (not set at construction time)
#     state: str = field(default=VMState.CREATED, init=False, repr=False)
#     host: Optional["Host"] = field(default=None, init=False, repr=False)
#     cloudlets: List["Cloudlet"] = field(default_factory=list, init=False, repr=False)

#     # Timing
#     start_time: float = field(default=0.0, init=False, repr=False)
#     finish_time: float = field(default=0.0, init=False, repr=False)

#     # Utilization tracking
#     _cpu_util_samples: List[float] = field(
#         default_factory=list, init=False, repr=False
#     )

#     @property
#     def total_mips(self) -> float:
#         """Total compute capacity: mips × number of PEs."""
#         return self.mips * self.pes

#     def record_cpu_utilization(self, utilization: float) -> None:
#         """
#         Record a CPU utilization sample (0.0 – 1.0).

#         Args:
#             utilization: Fraction of total MIPS currently in use.
#         """
#         self._cpu_util_samples.append(max(0.0, min(1.0, utilization)))

#     def average_cpu_utilization(self) -> float:
#         """Return the mean CPU utilization across all recorded samples."""
#         if not self._cpu_util_samples:
#             return 0.0
#         return sum(self._cpu_util_samples) / len(self._cpu_util_samples)

#     def is_running(self) -> bool:
#         """Return True if the VM is in the RUNNING state."""
#         return self.state == VMState.RUNNING

#     def __hash__(self) -> int:
#         return hash(self.vm_id)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from cloudsim.core.constants import VMState

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.hosts.host import Host


@dataclass
class VM:
    """
    PyCloudSim Virtual Machine
    """

    vm_id: int
    mips: float
    pes: int
    ram: int
    bandwidth: int
    storage: int
    broker_id: int = -1

    # Runtime state
    state: str = field(default=VMState.CREATED, init=False)
    host: Optional["Host"] = field(default=None, init=False)

    cloudlets: List["Cloudlet"] = field(default_factory=list, init=False)
    running_cloudlets: List["Cloudlet"] = field(default_factory=list, init=False)

    start_time: float = field(default=0.0, init=False)
    finish_time: float = field(default=0.0, init=False)

    # Resource tracking
    used_mips: float = field(default=0.0, init=False)
    used_ram: int = field(default=0, init=False)
    used_storage: int = field(default=0, init=False)
    used_bandwidth: int = field(default=0, init=False)

    # Historical samples
    cpu_samples: List[float] = field(default_factory=list, init=False)
    ram_samples: List[float] = field(default_factory=list, init=False)
    storage_samples: List[float] = field(default_factory=list, init=False)
    bandwidth_samples: List[float] = field(default_factory=list, init=False)

    @property
    def total_mips(self) -> float:
        return self.mips * self.pes

    @property
    def cpu_load(self) -> float:
        if self.total_mips <= 0:
            return 0.0
        return min(1.0, self.used_mips / self.total_mips)

    @property
    def ram_load(self) -> float:
        if self.ram <= 0:
            return 0.0
        return min(1.0, self.used_ram / self.ram)

    @property
    def storage_load(self) -> float:
        if self.storage <= 0:
            return 0.0
        return min(1.0, self.used_storage / self.storage)

    @property
    def bandwidth_load(self) -> float:
        if self.bandwidth <= 0:
            return 0.0
        return min(1.0, self.used_bandwidth / self.bandwidth)

    def assign_cloudlet(self, cloudlet: "Cloudlet") -> None:

        ram_req = getattr(cloudlet, "ram_required", 512)
        storage_req = getattr(cloudlet, "storage_required", 100)
        bw_req = getattr(cloudlet, "bandwidth_required", 100)

        if self.used_ram + ram_req > self.ram:
            raise RuntimeError(
                f"VM {self.vm_id} RAM capacity exceeded"
            )

        if self.used_storage + storage_req > self.storage:
            raise RuntimeError(
                f"VM {self.vm_id} storage capacity exceeded"
            )

        if self.used_bandwidth + bw_req > self.bandwidth:
            raise RuntimeError(
                f"VM {self.vm_id} bandwidth capacity exceeded"
            )

        self.running_cloudlets.append(cloudlet)

        self.used_ram += ram_req
        self.used_storage += storage_req
        self.used_bandwidth += bw_req

        self.update_used_mips()

        # print(f"Assgin -> VM={self.vm_id}"
        #       f"Cloudlet = {cloudlet.cloudlet_id}")

    def complete_cloudlet(self, cloudlet: "Cloudlet") -> None:

        if cloudlet not in self.running_cloudlets:
            return

        self.running_cloudlets.remove(cloudlet)

        ram_req = getattr(cloudlet, "ram_required", 512)
        storage_req = getattr(cloudlet, "storage_required", 100)
        bw_req = getattr(cloudlet, "bandwidth_required", 100)

        self.used_ram = max(0, self.used_ram - ram_req)
        self.used_storage = max(0, self.used_storage - storage_req)
        self.used_bandwidth = max(0, self.used_bandwidth - bw_req)

        self.update_used_mips()

        # print(
        #     f"UPDATE MIPS VM={self.vm_id} "
        #     f"running={len(self.running_cloudlets)}"
        # )

    # def update_used_mips(self) -> None:

    #     self.used_mips = sum(
    #         getattr(cl, "current_mips", 0.0)
    #         for cl in self.running_cloudlets
    #     )

    def update_used_mips(self):

        self.used_mips = sum(
            getattr(cl, "current_mips", 0.0)
            for cl in self.running_cloudlets
        )

        # print(
        #     f"VM {self.vm_id} | "
        #     f"running={len(self.running_cloudlets)} | "
        #     f"used_mips={self.used_mips}"
        # )

        # for cl in self.running_cloudlets:
        #     print(
        #         f"  Cloudlet={cl.cloudlet_id} "
        #         f"current_mips={cl.current_mips}"
        #     )
    
    def record_utilization_sample(self) -> None:

        self.cpu_samples.append(self.cpu_load)
        self.ram_samples.append(self.ram_load)
        self.storage_samples.append(self.storage_load)
        self.bandwidth_samples.append(self.bandwidth_load)

    def average_cpu_utilization(self) -> float:

        if not self.cpu_samples:
            return 0.0

        return sum(self.cpu_samples) / len(self.cpu_samples)

    def average_ram_utilization(self) -> float:

        if not self.ram_samples:
            return 0.0

        return sum(self.ram_samples) / len(self.ram_samples)

    def average_storage_utilization(self) -> float:

        if not self.storage_samples:
            return 0.0

        return sum(self.storage_samples) / len(self.storage_samples)

    def average_bandwidth_utilization(self) -> float:

        if not self.bandwidth_samples:
            return 0.0

        return sum(self.bandwidth_samples) / len(self.bandwidth_samples)

    def is_running(self) -> bool:
        return self.state == VMState.RUNNING

    def __hash__(self) -> int:
        return hash(self.vm_id)