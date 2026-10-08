"""
PyCloudSim Utilization Metrics Collector.

Stores VM and Host utilization snapshots throughout the simulation.
"""

from __future__ import annotations

from statistics import mean


class UtilizationCollector:

    def __init__(self) -> None:

        self.vm_samples = []

        self.host_samples = []

    # ---------------------------------------------------------
    # Snapshot Recording
    # ---------------------------------------------------------

    def record_vm_snapshot(
        self,
        timestamp: float,
        vm
    ) -> None:

        self.vm_samples.append(
            {
                "time": timestamp,
                "vm_id": vm.vm_id,
                "cpu_load": vm.cpu_load,
                "ram_load": vm.ram_load,
                "storage_load": vm.storage_load,
                "bandwidth_load": vm.bandwidth_load,
            }
        )

    def record_host_snapshot(
        self,
        timestamp: float,
        host
    ) -> None:

        self.host_samples.append(
            {
                "time": timestamp,
                "host_id": host.host_id,
                "cpu_load": host.cpu_load,
                "ram_load": host.ram_load,
                "storage_load": host.storage_load,
                "bandwidth_load": host.bandwidth_load,
            }
        )

    # ---------------------------------------------------------
    # VM Averages
    # ---------------------------------------------------------

    def average_vm_cpu_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return mean(
            sample["cpu_load"]
            for sample in self.vm_samples
        )

    def average_vm_ram_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return mean(
            sample["ram_load"]
            for sample in self.vm_samples
        )

    def average_vm_storage_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return mean(
            sample["storage_load"]
            for sample in self.vm_samples
        )

    def average_vm_bandwidth_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return mean(
            sample["bandwidth_load"]
            for sample in self.vm_samples
        )

    # ---------------------------------------------------------
    # Host Averages
    # ---------------------------------------------------------

    def average_host_cpu_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return mean(
            sample["cpu_load"]
            for sample in self.host_samples
        )

    def average_host_ram_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return mean(
            sample["ram_load"]
            for sample in self.host_samples
        )

    def average_host_storage_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return mean(
            sample["storage_load"]
            for sample in self.host_samples
        )

    def average_host_bandwidth_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return mean(
            sample["bandwidth_load"]
            for sample in self.host_samples
        )

    # ---------------------------------------------------------
    # Peak VM Utilization
    # ---------------------------------------------------------

    def peak_vm_cpu_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return max(
            sample["cpu_load"]
            for sample in self.vm_samples
        )

    def peak_vm_ram_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return max(
            sample["ram_load"]
            for sample in self.vm_samples
        )

    def peak_vm_storage_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return max(
            sample["storage_load"]
            for sample in self.vm_samples
        )

    def peak_vm_bandwidth_utilization(self) -> float:

        if not self.vm_samples:
            return 0.0

        return max(
            sample["bandwidth_load"]
            for sample in self.vm_samples
        )

    # ---------------------------------------------------------
    # Peak Host Utilization
    # ---------------------------------------------------------

    def peak_host_cpu_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return max(
            sample["cpu_load"]
            for sample in self.host_samples
        )

    def peak_host_ram_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return max(
            sample["ram_load"]
            for sample in self.host_samples
        )

    def peak_host_storage_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return max(
            sample["storage_load"]
            for sample in self.host_samples
        )

    def peak_host_bandwidth_utilization(self) -> float:

        if not self.host_samples:
            return 0.0

        return max(
            sample["bandwidth_load"]
            for sample in self.host_samples
        )

    # ---------------------------------------------------------
    # Export Helpers
    # ---------------------------------------------------------

    def vm_snapshot_count(self) -> int:

        return len(self.vm_samples)

    def host_snapshot_count(self) -> int:

        return len(self.host_samples)

    def clear(self) -> None:

        self.vm_samples.clear()

        self.host_samples.clear()