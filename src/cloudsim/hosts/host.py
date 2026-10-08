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
    """Physical host machine that provides resources to VMs."""

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
    _power_samples: List[float] = field(default_factory=list, init=False, repr=False)
    _cpu_samples: List[float] = field(default_factory=list, init=False, repr=False)
    _ram_samples: List[float] = field(default_factory=list, init=False, repr=False)
    _storage_samples: List[float] = field(default_factory=list, init=False, repr=False)
    _bw_samples: List[float] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.cpu_provisioner is None:
            self.cpu_provisioner = CPUProvisioner(capacity=self.mips * self.pes)
        if self.ram_provisioner is None:
            self.ram_provisioner = RAMProvisioner(capacity=self.ram)
        if self.bw_provisioner is None:
            self.bw_provisioner = BWProvisioner(capacity=self.bandwidth)

    @property
    def total_mips(self) -> float:
        return self.mips * self.pes

    @property
    def available_mips(self) -> float:
        return self.cpu_provisioner.available

    @property
    def cpu_load(self) -> float:
        if self.total_mips <= 0:
            return 0.0
        used = sum(vm.used_mips for vm in self.vms)
        return min(1.0, used / self.total_mips)

    @property
    def ram_load(self) -> float:
        if self.ram <= 0:
            return 0.0
        used = sum(vm.used_ram for vm in self.vms)
        return min(1.0, used / self.ram)

    @property
    def storage_load(self) -> float:
        if self.storage <= 0:
            return 0.0
        used = sum(vm.used_storage for vm in self.vms)
        return min(1.0, used / self.storage)

    @property
    def bandwidth_load(self) -> float:
        if self.bandwidth <= 0:
            return 0.0
        used = sum(vm.used_bandwidth for vm in self.vms)
        return min(1.0, used / self.bandwidth)

    @property
    def cpu_utilization(self) -> float:
        return self.cpu_load

    def is_suitable_for_vm(self, vm: "VM") -> bool:
        return (
            self.cpu_provisioner.is_suitable(vm.total_mips)
            and self.ram_provisioner.is_suitable(vm.ram)
            and self.bw_provisioner.is_suitable(vm.bandwidth)
            and self.storage >= vm.storage
        )

    def allocate_resources_for_vm(self, vm: "VM") -> bool:
        if not self.is_suitable_for_vm(vm):
            return False

        ok_cpu = self.cpu_provisioner.allocate(vm.vm_id, vm.total_mips)
        ok_ram = self.ram_provisioner.allocate(vm.vm_id, vm.ram)
        ok_bw = self.bw_provisioner.allocate(vm.vm_id, vm.bandwidth)

        if ok_cpu and ok_ram and ok_bw:
            vm.host = self
            vm.state = VMState.RUNNING
            self.vms.append(vm)
            return True

        self.cpu_provisioner.deallocate(vm.vm_id)
        self.ram_provisioner.deallocate(vm.vm_id)
        self.bw_provisioner.deallocate(vm.vm_id)
        return False

    def deallocate_resources_for_vm(self, vm: "VM") -> None:
        self.cpu_provisioner.deallocate(vm.vm_id)
        self.ram_provisioner.deallocate(vm.vm_id)
        self.bw_provisioner.deallocate(vm.vm_id)
        vm.host = None
        vm.state = VMState.DESTROYED
        if vm in self.vms:
            self.vms.remove(vm)

    def record_utilization_sample(self) -> None:
        self._cpu_samples.append(self.cpu_load)
        self._ram_samples.append(self.ram_load)
        self._storage_samples.append(self.storage_load)
        self._bw_samples.append(self.bandwidth_load)

    def average_cpu_utilization(self) -> float:
        if not self._cpu_samples:
            return 0.0
        return sum(self._cpu_samples) / len(self._cpu_samples)

    def average_ram_utilization(self) -> float:
        if not self._ram_samples:
            return 0.0
        return sum(self._ram_samples) / len(self._ram_samples)

    def average_storage_utilization(self) -> float:
        if not self._storage_samples:
            return 0.0
        return sum(self._storage_samples) / len(self._storage_samples)

    def average_bandwidth_utilization(self) -> float:
        if not self._bw_samples:
            return 0.0
        return sum(self._bw_samples) / len(self._bw_samples)

    def record_power(self, power_watts: float) -> None:
        self._power_samples.append(power_watts)

    def average_power(self) -> float:
        if not self._power_samples:
            return 0.0
        return sum(self._power_samples) / len(self._power_samples)

    def __hash__(self) -> int:
        return hash(self.host_id)


@dataclass
class PowerHost(Host):
    """Host with a linear power consumption model."""

    idle_power: float = 100.0
    max_power: float = 250.0

    def current_power(self) -> float:
        return self.idle_power + (self.max_power - self.idle_power) * self.cpu_load
