"""
PyCloudSim Metrics Module.

Collects, computes, and exports simulation metrics including makespan,
throughput, utilization, energy, cost, and SLA violations.
"""

from __future__ import annotations
import csv
import json
import os
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM
    from cloudsim.hosts.host import Host
    from cloudsim.datacenters.datacenter import Datacenter

logger = logging.getLogger(__name__)


@dataclass
class SimulationMetrics:
    """
    Aggregated metrics snapshot produced at the end of a simulation run.

    Attributes:
        makespan:           Time from first cloudlet start to last finish (s).
        throughput:         Cloudlets completed per unit time.
        total_cloudlets:    Number of cloudlets submitted.
        completed_cloudlets: Number of cloudlets that finished successfully.
        avg_execution_time: Mean cloudlet execution time (s).
        avg_waiting_time:   Mean queue wait after submission (start - submit) in seconds.
        avg_response_time:  Mean cloudlet response time (s).
        avg_cpu_utilization: Mean CPU utilisation across all VMs (fraction).
        total_energy_wh:    Estimated total energy in Watt-hours.
        total_cost:         Estimated monetary cost.
        sla_violations:     Number of cloudlets that missed their deadline.
        load_balance_index: Coefficient of variation of VM loads (lower = better balance).
    """

    makespan: float = 0.0
    throughput: float = 0.0
    total_cloudlets: int = 0
    completed_cloudlets: int = 0
    avg_execution_time: float = 0.0
    avg_waiting_time: float = 0.0
    avg_response_time: float = 0.0
    avg_cpu_utilization: float = 0.0
    total_energy_wh: float = 0.0
    total_cost: float = 0.0
    sla_violations: int = 0
    load_balance_index: float = 0.0


class MetricsCollector:
    """
    Computes and exports simulation metrics.

    Example:
        >>> collector = MetricsCollector()
        >>> metrics = collector.compute(cloudlets, vms, datacenter, sim_end_time)
        >>> collector.export_csv(metrics, "results/csv/metrics.csv")
        >>> collector.export_json(metrics, "results/json/metrics.json")
    """

    def compute(
        self,
        cloudlets: List["Cloudlet"],
        vms: List["VM"],
        datacenter: Optional["Datacenter"] = None,
        sim_end_time: float = 0.0,
    ) -> SimulationMetrics:
        """
        Compute all metrics from completed cloudlets and VMs.

        Args:
            cloudlets:    All submitted cloudlets (completed or not).
            vms:          All VMs used during the simulation.
            datacenter:   Optional datacenter for energy/cost calculation.
            sim_end_time: Clock time when the simulation ended.

        Returns:
            A populated SimulationMetrics instance.
        """
        from cloudsim.core.constants import CloudletState

        completed = [cl for cl in cloudlets if cl.state == CloudletState.SUCCESS]
        total = len(cloudlets)
        n_done = len(completed)

        makespan = 0.0
        if completed:
            first_start = min(cl.start_time for cl in completed)
            last_finish = max(cl.finish_time for cl in completed)
            makespan = last_finish - first_start

        throughput = n_done / makespan if makespan > 0 else 0.0

        avg_exec = sum(cl.execution_time for cl in completed) / n_done if n_done else 0.0
        avg_wait = sum(cl.waiting_time for cl in completed) / n_done if n_done else 0.0
        avg_resp = sum(cl.response_time for cl in completed) / n_done if n_done else 0.0

        sla_violations = sum(1 for cl in completed if cl.sla_violated)

        # VM CPU utilization
        util_samples = [vm.average_cpu_utilization() for vm in vms]
        avg_util = sum(util_samples) / len(util_samples) if util_samples else 0.0

        # Load balance index (coefficient of variation of cloudlets per VM)
        vm_loads = [len(vm.cloudlets) for vm in vms]
        if vm_loads and len(vm_loads) > 1:
            mean_load = sum(vm_loads) / len(vm_loads)
            variance = sum((x - mean_load) ** 2 for x in vm_loads) / len(vm_loads)
            std_dev = variance ** 0.5
            lbi = std_dev / mean_load if mean_load > 0 else 0.0
        else:
            lbi = 0.0

        # Energy & cost
        energy = 0.0
        cost = 0.0
        if datacenter:
            energy = datacenter.total_energy(sim_end_time)
            for cl in completed:
                cost += datacenter.characteristics.compute_cost(
                    cl.execution_time,
                    next((v.ram for v in vms if v.vm_id == cl.assigned_vm_id), 0.0),
                    0.0,
                    0.0,
                )

        return SimulationMetrics(
            makespan=makespan,
            throughput=throughput,
            total_cloudlets=total,
            completed_cloudlets=n_done,
            avg_execution_time=avg_exec,
            avg_waiting_time=avg_wait,
            avg_response_time=avg_resp,
            avg_cpu_utilization=avg_util,
            total_energy_wh=energy,
            total_cost=cost,
            sla_violations=sla_violations,
            load_balance_index=lbi,
        )

    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------

    def export_csv(
        self,
        metrics: SimulationMetrics,
        cloudlets: List["Cloudlet"],
        path: str,
    ) -> None:
        """
        Export per-cloudlet results and summary metrics to CSV files.

        Args:
            metrics:   Aggregated metrics.
            cloudlets: All cloudlets.
            path:      Directory path for CSV output.
        """
        os.makedirs(path, exist_ok=True)

        # Per-cloudlet CSV
        cl_path = os.path.join(path, "cloudlets.csv")
        with open(cl_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "id", "state", "vm_id", "length", "pes",
                "arrival", "submit", "start", "finish",
                "exec_time", "wait_time", "response_time", "sla_violated",
            ])
            for cl in cloudlets:
                writer.writerow([
                    cl.cloudlet_id, cl.state, cl.assigned_vm_id,
                    cl.length, cl.pes,
                    cl.arrival_time, cl.submit_time, cl.start_time, cl.finish_time,
                    cl.execution_time, cl.waiting_time, cl.response_time,
                    cl.sla_violated,
                ])
        logger.info("Cloudlet results exported → %s", cl_path)

        # Summary metrics CSV
        summary_path = os.path.join(path, "summary.csv")
        d = asdict(metrics)
        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            for k, v in d.items():
                writer.writerow([k, v])
        logger.info("Summary metrics exported → %s", summary_path)

    def export_json(
        self,
        metrics: SimulationMetrics,
        cloudlets: List["Cloudlet"],
        path: str,
    ) -> None:
        """
        Export metrics and cloudlet results to JSON files.

        Args:
            metrics:   Aggregated metrics.
            cloudlets: All cloudlets.
            path:      Directory path for JSON output.
        """
        os.makedirs(path, exist_ok=True)

        summary_path = os.path.join(path, "summary.json")
        with open(summary_path, "w") as f:
            json.dump(asdict(metrics), f, indent=2)
        logger.info("JSON metrics exported → %s", summary_path)

        cl_path = os.path.join(path, "cloudlets.json")
        cl_data = [
            {
                "id": cl.cloudlet_id,
                "state": cl.state,
                "vm_id": cl.assigned_vm_id,
                "length": cl.length,
                "pes": cl.pes,
                "arrival_time": cl.arrival_time,
                "submit_time": cl.submit_time,
                "start_time": cl.start_time,
                "finish_time": cl.finish_time,
                "execution_time": cl.execution_time,
                "waiting_time": cl.waiting_time,
                "response_time": cl.response_time,
                "sla_violated": cl.sla_violated,
            }
            for cl in cloudlets
        ]
        with open(cl_path, "w") as f:
            json.dump(cl_data, f, indent=2)
        logger.info("JSON cloudlets exported → %s", cl_path)

    def generate_plots(
        self,
        metrics: SimulationMetrics,
        cloudlets: List["Cloudlet"],
        vms: List["VM"],
        path: str,
    ) -> None:
        """
        Generate and save Matplotlib plots for key metrics.

        Args:
            metrics:   Aggregated metrics.
            cloudlets: All cloudlets.
            vms:       All VMs.
            path:      Directory path for plot output.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not installed; skipping plot generation.")
            return

        os.makedirs(path, exist_ok=True)
        from cloudsim.core.constants import CloudletState
        completed = [cl for cl in cloudlets if cl.state == CloudletState.SUCCESS]

        # --- Execution time histogram ---
        if completed:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.hist([cl.execution_time for cl in completed], bins=20, color="steelblue", edgecolor="white")
            ax.set_xlabel("Execution Time (s)")
            ax.set_ylabel("Frequency")
            ax.set_title("Cloudlet Execution Time Distribution")
            fig.tight_layout()
            fig.savefig(os.path.join(path, "exec_time_hist.png"), dpi=150)
            plt.close(fig)

        # --- Cloudlets per VM bar chart ---
        vm_ids = [vm.vm_id for vm in vms]
        vm_cl_counts = [len(vm.cloudlets) for vm in vms]
        fig, ax = plt.subplots(figsize=(max(6, len(vms)), 4))
        ax.bar([f"VM {v}" for v in vm_ids], vm_cl_counts, color="coral", edgecolor="white")
        ax.set_xlabel("VM")
        ax.set_ylabel("Cloudlets Assigned")
        ax.set_title("Cloudlet Distribution Across VMs")
        fig.tight_layout()
        fig.savefig(os.path.join(path, "vm_load.png"), dpi=150)
        plt.close(fig)

        # --- Gantt-style response time scatter ---
        if completed:
            fig, ax = plt.subplots(figsize=(10, 4))
            ids = [cl.cloudlet_id for cl in completed]
            ax.barh(
                ids,
                [cl.execution_time for cl in completed],
                left=[cl.start_time for cl in completed],
                height=0.6,
                color="mediumseagreen",
                label="Execution",
            )
            ax.set_xlabel("Simulation Time (s)")
            ax.set_ylabel("Cloudlet ID")
            ax.set_title("Cloudlet Execution Timeline (Gantt)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(os.path.join(path, "gantt.png"), dpi=150)
            plt.close(fig)

        logger.info("Plots saved to %s", path)
