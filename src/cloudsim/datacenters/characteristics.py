"""
PyCloudSim Datacenter Characteristics Module.

Holds the pricing and SLA characteristics of a Datacenter.
"""

from __future__ import annotations
from dataclasses import dataclass

from cloudsim.core.constants import (
    DEFAULT_COST_PER_SECOND,
    DEFAULT_COST_PER_MEM,
    DEFAULT_COST_PER_STORAGE,
    DEFAULT_COST_PER_BW,
)


@dataclass
class DatacenterCharacteristics:
    """
    Describes the cost and SLA properties of a Datacenter.

    Attributes:
        architecture:       Hardware architecture string (e.g. "x86").
        os:                 Operating system string (e.g. "Linux").
        vmm:                Virtual machine monitor (e.g. "KVM").
        cost_per_second:    Cost per second of VM execution ($/s).
        cost_per_mem:       Cost per MB of RAM per second.
        cost_per_storage:   Cost per MB of storage per second.
        cost_per_bw:        Cost per Mbps of bandwidth per second.
        time_zone:          Timezone offset from UTC.
    """

    architecture: str = "x86"
    os: str = "Linux"
    vmm: str = "KVM"
    cost_per_second: float = DEFAULT_COST_PER_SECOND
    cost_per_mem: float = DEFAULT_COST_PER_MEM
    cost_per_storage: float = DEFAULT_COST_PER_STORAGE
    cost_per_bw: float = DEFAULT_COST_PER_BW
    time_zone: float = 0.0

    def compute_cost(
        self,
        exec_time: float,
        ram_mb: float,
        storage_mb: float,
        bw_mbps: float,
    ) -> float:
        """
        Compute the monetary cost for a VM or cloudlet.

        Args:
            exec_time:  Execution duration in seconds.
            ram_mb:     RAM used in MB.
            storage_mb: Storage used in MB.
            bw_mbps:    Bandwidth used in Mbps.

        Returns:
            Estimated cost in dollars.
        """
        return (
            exec_time * self.cost_per_second
            + ram_mb * self.cost_per_mem
            + storage_mb * self.cost_per_storage
            + bw_mbps * self.cost_per_bw
        )
