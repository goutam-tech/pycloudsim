"""Tests for cloudlet waiting time metrics."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cloudsim.cloudlets.cloudlet import Cloudlet
from cloudsim.cloudlets.task_loader import TaskLoader
from cloudsim.core.constants import DEFAULT_SCHEDULING_INTERVAL
from cloudsim.core.simulation import Simulation
from cloudsim.datacenters.broker import DatacenterBroker
from cloudsim.datacenters.characteristics import DatacenterCharacteristics
from cloudsim.datacenters.datacenter import Datacenter
from cloudsim.hosts.host_loader import HostLoader
from cloudsim.metrics.metrics import MetricsCollector
from cloudsim.vms.vm_loader import VMLoader
from algorithms.scheduling.round_robin import RoundRobinScheduler


def _run_simulation(cloudlet_path: str) -> tuple[list[Cloudlet], object]:
    sim = Simulation()
    hosts = HostLoader.load("datasets/hosts/hosts.json")
    datacenter = Datacenter(
        name="DC-test",
        hosts=hosts,
        characteristics=DatacenterCharacteristics(),
        scheduling_interval=DEFAULT_SCHEDULING_INTERVAL,
    )
    sim.add_entity(datacenter)

    broker = DatacenterBroker(name="Broker-test", scheduler=RoundRobinScheduler())
    sim.add_entity(broker)
    broker.add_datacenter(datacenter)

    vms = VMLoader.load("datasets/vms/vms.json")
    cloudlets = TaskLoader.load(cloudlet_path)
    broker.submit_vm_list(vms)
    broker.submit_cloudlet_list(cloudlets)

    sim.run()

    collector = MetricsCollector()
    metrics = collector.compute(
        cloudlets=cloudlets,
        vms=vms,
        datacenter=datacenter,
        sim_end_time=sim.clock.now(),
    )
    return cloudlets, metrics


def test_waiting_time_property_uses_submit_time() -> None:
    cloudlet = Cloudlet(cloudlet_id=1, length=1000, arrival_time=0.0)
    cloudlet.submit_time = 2.0
    cloudlet.start_time = 5.0
    cloudlet.finish_time = 7.0

    assert cloudlet.waiting_time == pytest.approx(3.0)
    assert cloudlet.response_time == pytest.approx(5.0)
    assert cloudlet.execution_time == pytest.approx(2.0)


def test_simulation_reports_nonzero_avg_waiting_time() -> None:
    cloudlets, metrics = _run_simulation("datasets/cloudlets/cloudlets.json")

    assert metrics.completed_cloudlets == len(cloudlets)
    assert metrics.avg_waiting_time > 0.0

    queued = [cl for cl in cloudlets if cl.waiting_time > 0]
    assert queued, "Expected at least one cloudlet with queue wait"


def test_first_cloudlet_on_idle_vm_has_zero_wait() -> None:
    cloudlets, _ = _run_simulation("datasets/cloudlets/cloudlets.json")
    first_on_vm = {}
    for cloudlet in sorted(cloudlets, key=lambda cl: (cl.assigned_vm_id, cl.start_time)):
        if cloudlet.assigned_vm_id not in first_on_vm:
            first_on_vm[cloudlet.assigned_vm_id] = cloudlet

    for cloudlet in first_on_vm.values():
        assert cloudlet.waiting_time == pytest.approx(0.0)
