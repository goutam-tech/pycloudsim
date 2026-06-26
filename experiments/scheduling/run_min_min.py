"""
Min Min Scheduling Experiment.

Run with:
    python experiments/scheduling/run_min_min.py
"""

from __future__ import annotations
import logging
import sys
import os
import time

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path when run directly
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# ---------------------------------------------------------------------------
# Silence verbose internal logging; use Rich for user-facing output
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from cloudsim.core.simulation import Simulation
from cloudsim.core.constants import DEFAULT_SCHEDULING_INTERVAL

from cloudsim.hosts.host import PowerHost
from cloudsim.vms.vm import VM
from cloudsim.cloudlets.cloudlet import Cloudlet
# from cloudsim.cloudlets.task_generator import TaskGenerator

import json
import datasets.cloudlets
import datasets.hosts
import datasets.vms
from cloudsim.cloudlets.task_loader import TaskLoader
from cloudsim.hosts.host_loader import HostLoader
from cloudsim.vms.vm_loader import VMLoader

from cloudsim.datacenters.datacenter import Datacenter
from cloudsim.datacenters.broker import DatacenterBroker
from cloudsim.datacenters.characteristics import DatacenterCharacteristics

from cloudsim.metrics.metrics import MetricsCollector

from cloudsim.utils.logger import (
    print_banner,
    info,
    success,
    warning,
    metric,
    print_metrics_table,
    print_cloudlet_table,
    make_progress,
    console,
)
from rich.panel import Panel

from algorithms.scheduling.min_min import MinMinScheduler

def run() -> None:
    """Execute the Round Robin scheduling experiment."""
    print_banner("PyCloudSim — Round Robin Experiment")
    console.print()

    with make_progress() as progress:
        task = progress.add_task("[cyan]Setting up simulation…", total=7)

        # 1. Simulation engine
        sim = Simulation()
        progress.advance(task)

        # 2. Hosts & Datacenter
        hosts = HostLoader.load(
            "datasets/hosts/hosts.json"
        )
        characteristics = DatacenterCharacteristics(
            architecture="x86_64",
            os="Ubuntu 22.04",
            vmm="KVM",
            cost_per_second=0.01,
            cost_per_mem=0.002,
            cost_per_storage=0.0001,
            cost_per_bw=0.0005,
        )
        datacenter = Datacenter(
            name="DC-1",
            hosts=hosts,
            characteristics=characteristics,
            scheduling_interval=DEFAULT_SCHEDULING_INTERVAL,
        )
        sim.add_entity(datacenter)
        progress.advance(task)

        # 3. Scheduler & Broker
        scheduler = MinMinScheduler()
        broker = DatacenterBroker(name="Broker-1", scheduler=scheduler)
        sim.add_entity(broker)
        broker.add_datacenter(datacenter)
        progress.advance(task)

        # 4. VMs
        vms = VMLoader.load(
            "datasets/vms/vms.json"
        )
        broker.submit_vm_list(vms)
        progress.advance(task)

        # 5. Cloudlets
        cloudlets = TaskLoader.load(
            "datasets/cloudlets/cloudlets.json"
        )
        broker.submit_cloudlet_list(cloudlets)
        progress.advance(task)

        # 6. Run simulation
        progress.update(task, description="[cyan]Running simulation…")
        wall_start = time.perf_counter()
        sim.run()
        wall_elapsed = time.perf_counter() - wall_start
        progress.advance(task)

        # 7. Collect metrics
        progress.update(task, description="[cyan]Computing metrics…")
        collector = MetricsCollector()
        sim_end_time = sim.clock.now()
        metrics = collector.compute(
            cloudlets=cloudlets,
            vms=vms,
            datacenter=datacenter,
            sim_end_time=sim_end_time,
        )
        progress.advance(task)

    console.print()
    success(f"Simulation completed in {wall_elapsed:.3f}s (sim time={sim_end_time:.4f}s)")
    info(f"Events processed: {sim.total_events_processed}")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    console.print()
    console.print(Panel("[bold]Validation Checks[/bold]", border_style="blue"))

    if metrics.makespan > 0:
        success(f"Makespan > 0  ✓  ({metrics.makespan:.4f}s)")
    else:
        warning("Makespan is zero — no cloudlets completed!")

    if metrics.completed_cloudlets == metrics.total_cloudlets:
        success(f"All {metrics.total_cloudlets} cloudlets completed ✓")
    else:
        warning(
            f"Only {metrics.completed_cloudlets}/{metrics.total_cloudlets} cloudlets completed"
        )

    # Check VM utilisation calculated
    for vm in vms:
        util = vm.average_cpu_utilization()
        metric(f"VM {vm.vm_id}: avg CPU utilisation = {util*100:.1f}%  |  cloudlets = {len(vm.cloudlets)}")

    if metrics.sla_violations == 0:
        success("No SLA violations ✓")
    else:
        from cloudsim.utils.logger import error
        error(f"{metrics.sla_violations} SLA violation(s) detected!")

    # ------------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------------
    console.print()
    print_metrics_table(metrics)
    console.print()
    print_cloudlet_table(cloudlets)

    # ------------------------------------------------------------------
    # Export results
    # ------------------------------------------------------------------
    console.print()
    info("Exporting results…")

    collector.export_csv(metrics, cloudlets, path="results/csv")
    success("CSV results saved to results/csv/")

    collector.export_json(metrics, cloudlets, path="results/json")
    success("JSON results saved to results/json/")

    try:
        collector.generate_plots(metrics, cloudlets, vms, path="results/plots")
        success("Plots saved to results/plots/")
    except Exception as exc:
        warning(f"Plot generation skipped: {exc}")

    console.print()
    console.print(
        Panel(
            "[bold green]Experiment complete![/bold green]\n"
            "[dim]Results exported to results/csv/, results/json/, results/plots/[/dim]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    run()