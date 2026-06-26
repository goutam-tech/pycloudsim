# """
# PyCloudSim Host Module.

# Defines the Host entity that manages physical compute resources and hosts VMs.
# """

# from __future__ import annotations
# from dataclasses import dataclass, field
# from typing import List, Dict, Optional, TYPE_CHECKING

# from cloudsim.provisioners.provisioners import CPUProvisioner, RAMProvisioner, BWProvisioner
# from cloudsim.core.constants import VMState

# if TYPE_CHECKING:
#     from cloudsim.vms.vm import VM


# @dataclass
# class Host:
#     """
#     Physical host machine in a datacenter.

#     A Host provides CPU MIPS, RAM, bandwidth, and storage to VMs. Resource
#     allocation is mediated by the injected provisioner instances.

#     Attributes:
#         host_id:       Unique identifier.
#         mips:          MIPS per Processing Element.
#         pes:           Number of PEs (physical CPU cores).
#         ram:           Total RAM in MB.
#         bandwidth:     Total uplink bandwidth in Mbps.
#         storage:       Total disk storage in MB.
#         cpu_provisioner:  Provisioner managing MIPS allocation.
#         ram_provisioner:  Provisioner managing RAM allocation.
#         bw_provisioner:   Provisioner managing bandwidth allocation.
#     """

#     host_id: int
#     mips: float
#     pes: int
#     ram: float
#     bandwidth: float
#     storage: float
#     cpu_provisioner: CPUProvisioner = field(default=None)  # type: ignore[assignment]
#     ram_provisioner: RAMProvisioner = field(default=None)  # type: ignore[assignment]
#     bw_provisioner: BWProvisioner = field(default=None)    # type: ignore[assignment]

#     # Runtime
#     vms: List["VM"] = field(default_factory=list, init=False, repr=False)
#     _power_samples: List[float] = field(default_factory=list, init=False, repr=False)

#     def __post_init__(self) -> None:
#         if self.cpu_provisioner is None:
#             self.cpu_provisioner = CPUProvisioner(capacity=self.mips * self.pes)
#         if self.ram_provisioner is None:
#             self.ram_provisioner = RAMProvisioner(capacity=self.ram)
#         if self.bw_provisioner is None:
#             self.bw_provisioner = BWProvisioner(capacity=self.bandwidth)

#     @property
#     def total_mips(self) -> float:
#         """Total MIPS capacity of all PEs."""
#         return self.mips * self.pes

#     @property
#     def available_mips(self) -> float:
#         """Unallocated MIPS."""
#         return self.cpu_provisioner.available

#     @property
#     def cpu_utilization(self) -> float:
#         """Current CPU utilisation as a fraction (0.0 – 1.0)."""
#         used = self.total_mips - self.available_mips
#         return used / self.total_mips if self.total_mips > 0 else 0.0

#     def is_suitable_for_vm(self, vm: "VM") -> bool:
#         """
#         Check whether this host has enough resources to accommodate *vm*.

#         Args:
#             vm: The VM to evaluate.

#         Returns:
#             True if all resource checks pass.
#         """
#         return (
#             self.cpu_provisioner.is_suitable(vm.mips * vm.pes)
#             and self.ram_provisioner.is_suitable(vm.ram)
#             and self.bw_provisioner.is_suitable(vm.bandwidth)
#             and self.storage >= vm.storage
#         )

#     def allocate_resources_for_vm(self, vm: "VM") -> bool:
#         """
#         Allocate host resources to *vm* and register it.

#         Args:
#             vm: The VM to allocate resources for.

#         Returns:
#             True if all allocations succeeded.
#         """
#         if not self.is_suitable_for_vm(vm):
#             return False

#         ok_cpu = self.cpu_provisioner.allocate(vm.vm_id, vm.mips * vm.pes)
#         ok_ram = self.ram_provisioner.allocate(vm.vm_id, vm.ram)
#         ok_bw = self.bw_provisioner.allocate(vm.vm_id, vm.bandwidth)

#         if ok_cpu and ok_ram and ok_bw:
#             vm.host = self
#             vm.state = VMState.RUNNING
#             self.vms.append(vm)
#             return True

#         # Roll back partial allocations
#         self.cpu_provisioner.deallocate(vm.vm_id)
#         self.ram_provisioner.deallocate(vm.vm_id)
#         self.bw_provisioner.deallocate(vm.vm_id)
#         return False

#     def deallocate_resources_for_vm(self, vm: "VM") -> None:
#         """
#         Release resources and de-register *vm* from this host.

#         Args:
#             vm: The VM being destroyed or migrated.
#         """
#         self.cpu_provisioner.deallocate(vm.vm_id)
#         self.ram_provisioner.deallocate(vm.vm_id)
#         self.bw_provisioner.deallocate(vm.vm_id)
#         vm.host = None
#         vm.state = VMState.DESTROYED
#         if vm in self.vms:
#             self.vms.remove(vm)

#     def record_power(self, power_watts: float) -> None:
#         """Record an instantaneous power reading in Watts."""
#         self._power_samples.append(power_watts)

#     def average_power(self) -> float:
#         """Return mean power consumption across all recorded samples (Watts)."""
#         if not self._power_samples:
#             return 0.0
#         return sum(self._power_samples) / len(self._power_samples)

#     def __hash__(self) -> int:
#         return hash(self.host_id)


# @dataclass
# class PowerHost(Host):
#     """
#     Host with a linear power model.

#     Power consumption is modeled as:
#         P = idle_power + (max_power - idle_power) × cpu_utilization

#     Attributes:
#         idle_power: Power draw at 0 % CPU utilisation (Watts).
#         max_power:  Power draw at 100 % CPU utilisation (Watts).
#     """

#     idle_power: float = 100.0
#     max_power: float = 250.0

#     def current_power(self) -> float:
#         """
#         Compute instantaneous power using a linear model.

#         Returns:
#             Power in Watts.
#         """
#         util = self.cpu_utilization
#         return self.idle_power + (self.max_power - self.idle_power) * util

"""
PyCloudSim Host Module.

Defines Host and PowerHost with runtime utilization tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from cloudsim.provisioners.provisioners import (
    CPUProvisioner,
    RAMProvisioner,
    BWProvisioner,
)
from cloudsim.core.constants import VMState

if TYPE_CHECKING:
    from cloudsim.vms.vm import VM


@dataclass
class Host:
    """
    Physical Host.
    """

    host_id: int
    mips: float
    pes: int
    ram: int
    bandwidth: int
    storage: int

    cpu_provisioner: CPUProvisioner = field(default=None)
    ram_provisioner: RAMProvisioner = field(default=None)
    bw_provisioner: BWProvisioner = field(default=None)

    vms: List["VM"] = field(default_factory=list, init=False)

    # Power history
    _power_samples: List[float] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    # Utilization history
    _cpu_samples: List[float] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    _ram_samples: List[float] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    _storage_samples: List[float] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    _bw_samples: List[float] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def __post_init__(self):

        if self.cpu_provisioner is None:
            self.cpu_provisioner = CPUProvisioner(
                capacity=self.mips * self.pes
            )

        if self.ram_provisioner is None:
            self.ram_provisioner = RAMProvisioner(
                capacity=self.ram
            )

        if self.bw_provisioner is None:
            self.bw_provisioner = BWProvisioner(
                capacity=self.bandwidth
            )

    # ---------------------------------------------------------
    # Capacity
    # ---------------------------------------------------------

    @property
    def total_mips(self) -> float:
        return self.mips * self.pes

    @property
    def available_mips(self) -> float:
        return self.cpu_provisioner.available

    # ---------------------------------------------------------
    # Runtime utilization
    # ---------------------------------------------------------

    @property
    def cpu_load(self) -> float:

        if self.total_mips <= 0:
            return 0.0

        used = sum(
            vm.used_mips
            for vm in self.vms
        )

        return min(1.0, used / self.total_mips)

    @property
    def ram_load(self) -> float:

        if self.ram <= 0:
            return 0.0

        used = sum(
            vm.used_ram
            for vm in self.vms
        )

        return min(1.0, used / self.ram)

    @property
    def storage_load(self) -> float:

        if self.storage <= 0:
            return 0.0

        used = sum(
            vm.used_storage
            for vm in self.vms
        )

        return min(1.0, used / self.storage)

    @property
    def bandwidth_load(self) -> float:

        if self.bandwidth <= 0:
            return 0.0

        used = sum(
            vm.used_bandwidth
            for vm in self.vms
        )

        return min(1.0, used / self.bandwidth)

    # Backward compatibility
    @property
    def cpu_utilization(self) -> float:
        return self.cpu_load

    # ---------------------------------------------------------
    # VM allocation
    # ---------------------------------------------------------

    def is_suitable_for_vm(self, vm: "VM") -> bool:

        return (
            self.cpu_provisioner.is_suitable(
                vm.total_mips
            )
            and self.ram_provisioner.is_suitable(
                vm.ram
            )
            and self.bw_provisioner.is_suitable(
                vm.bandwidth
            )
            and self.storage >= vm.storage
        )

    def allocate_resources_for_vm(
        self,
        vm: "VM"
    ) -> bool:

        if not self.is_suitable_for_vm(vm):
            return False

        ok_cpu = self.cpu_provisioner.allocate(
            vm.vm_id,
            vm.total_mips
        )

        ok_ram = self.ram_provisioner.allocate(
            vm.vm_id,
            vm.ram
        )

        ok_bw = self.bw_provisioner.allocate(
            vm.vm_id,
            vm.bandwidth
        )

        if ok_cpu and ok_ram and ok_bw:

            vm.host = self
            vm.state = VMState.RUNNING

            self.vms.append(vm)

            return True

        self.cpu_provisioner.deallocate(
            vm.vm_id
        )

        self.ram_provisioner.deallocate(
            vm.vm_id
        )

        self.bw_provisioner.deallocate(
            vm.vm_id
        )

        return False

    def deallocate_resources_for_vm(
        self,
        vm: "VM"
    ) -> None:

        self.cpu_provisioner.deallocate(
            vm.vm_id
        )

        self.ram_provisioner.deallocate(
            vm.vm_id
        )

        self.bw_provisioner.deallocate(
            vm.vm_id
        )

        vm.host = None
        vm.state = VMState.DESTROYED

        if vm in self.vms:
            self.vms.remove(vm)

    # ---------------------------------------------------------
    # Utilization recording
    # ---------------------------------------------------------

    def record_utilization_sample(self) -> None:

        self._cpu_samples.append(
            self.cpu_load
        )

        self._ram_samples.append(
            self.ram_load
        )

        self._storage_samples.append(
            self.storage_load
        )

        self._bw_samples.append(
            self.bandwidth_load
        )

    def average_cpu_utilization(self) -> float:

        if not self._cpu_samples:
            return 0.0

        return (
            sum(self._cpu_samples)
            / len(self._cpu_samples)
        )

    def average_ram_utilization(self) -> float:

        if not self._ram_samples:
            return 0.0

        return (
            sum(self._ram_samples)
            / len(self._ram_samples)
        )

    def average_storage_utilization(self) -> float:

        if not self._storage_samples:
            return 0.0

        return (
            sum(self._storage_samples)
            / len(self._storage_samples)
        )

    def average_bandwidth_utilization(self) -> float:

        if not self._bw_samples:
            return 0.0

        return (
            sum(self._bw_samples)
            / len(self._bw_samples)
        )

    # ---------------------------------------------------------
    # Power
    # ---------------------------------------------------------

    def record_power(
        self,
        power_watts: float
    ) -> None:

        self._power_samples.append(
            power_watts
        )

    def average_power(self) -> float:

        if not self._power_samples:
            return 0.0

        return (
            sum(self._power_samples)
            / len(self._power_samples)
        )

    def __hash__(self) -> int:
        return hash(self.host_id)


@dataclass
class PowerHost(Host):
    """
    Host with linear power model.
    """

    idle_power: float = 100.0
    max_power: float = 250.0

    def current_power(self) -> float:

        util = self.cpu_load

        return (
            self.idle_power
            + (
                self.max_power
                - self.idle_power
            )
            * util
        )