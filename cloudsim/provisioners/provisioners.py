"""
PyCloudSim Provisioners Module.

Implements CPU, RAM, and Bandwidth provisioners that manage resource
allocation on a Host for VMs.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Optional


class ResourceProvisioner(ABC):
    """
    Abstract base class for resource provisioners.

    A provisioner tracks how much of a resource is available on a Host and
    mediates allocation / deallocation for individual VMs.

    Args:
        capacity: Total capacity of the resource.
    """

    def __init__(self, capacity: float) -> None:
        self._capacity: float = capacity
        self._allocated: Dict[int, float] = {}  # vm_id -> allocated amount

    @property
    def capacity(self) -> float:
        """Total resource capacity."""
        return self._capacity

    @property
    def allocated(self) -> float:
        """Total currently allocated resource."""
        return sum(self._allocated.values())

    @property
    def available(self) -> float:
        """Remaining unallocated resource."""
        return self._capacity - self.allocated

    @abstractmethod
    def allocate(self, vm_id: int, amount: float) -> bool:
        """
        Attempt to allocate a resource for a VM.

        Args:
            vm_id: Identifier of the VM requesting the resource.
            amount: Amount of resource to allocate.

        Returns:
            True if allocation succeeded, False otherwise.
        """
        ...

    @abstractmethod
    def deallocate(self, vm_id: int) -> None:
        """
        Release resources previously allocated to a VM.

        Args:
            vm_id: Identifier of the VM releasing the resource.
        """
        ...

    def get_allocated_for_vm(self, vm_id: int) -> float:
        """Return the amount of resource allocated to a specific VM."""
        return self._allocated.get(vm_id, 0.0)

    def is_suitable(self, amount: float) -> bool:
        """Return True if *amount* can be allocated right now."""
        return amount <= self.available


class CPUProvisioner(ResourceProvisioner):
    """
    Provisioner for CPU MIPS capacity.

    Allocates CPU MIPS from a Host's total MIPS pool to VMs.

    Example:
        >>> prov = CPUProvisioner(capacity=10000.0)
        >>> prov.allocate(vm_id=0, amount=2000.0)
        True
    """

    def allocate(self, vm_id: int, amount: float) -> bool:
        """Allocate *amount* MIPS to *vm_id*. Returns False if insufficient."""
        if amount > self.available:
            return False
        self._allocated[vm_id] = self._allocated.get(vm_id, 0.0) + amount
        return True

    def deallocate(self, vm_id: int) -> None:
        """Release all MIPS allocated to *vm_id*."""
        self._allocated.pop(vm_id, None)


class RAMProvisioner(ResourceProvisioner):
    """
    Provisioner for RAM (MB).

    Allocates RAM from a Host's total RAM to VMs.

    Example:
        >>> prov = RAMProvisioner(capacity=65536)
        >>> prov.allocate(vm_id=0, amount=8192)
        True
    """

    def allocate(self, vm_id: int, amount: float) -> bool:
        """Allocate *amount* MB of RAM to *vm_id*."""
        if amount > self.available:
            return False
        self._allocated[vm_id] = amount
        return True

    def deallocate(self, vm_id: int) -> None:
        """Release RAM allocated to *vm_id*."""
        self._allocated.pop(vm_id, None)


class BWProvisioner(ResourceProvisioner):
    """
    Provisioner for network bandwidth (Mbps).

    Allocates bandwidth from a Host's uplink to VMs.

    Example:
        >>> prov = BWProvisioner(capacity=10000.0)
        >>> prov.allocate(vm_id=0, amount=1000.0)
        True
    """

    def allocate(self, vm_id: int, amount: float) -> bool:
        """Allocate *amount* Mbps to *vm_id*."""
        if amount > self.available:
            return False
        self._allocated[vm_id] = amount
        return True

    def deallocate(self, vm_id: int) -> None:
        """Release bandwidth allocated to *vm_id*."""
        self._allocated.pop(vm_id, None)
