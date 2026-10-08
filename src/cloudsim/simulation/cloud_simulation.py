from __future__ import annotations

from pathlib import Path

from cloudsim.core.constants import DEFAULT_SCHEDULING_INTERVAL
from cloudsim.core.simulation import Simulation
from cloudsim.cloudlets.task_loader import TaskLoader
from cloudsim.datacenters.broker import DatacenterBroker
from cloudsim.datacenters.characteristics import DatacenterCharacteristics
from cloudsim.datacenters.datacenter import Datacenter
from cloudsim.hosts.host_loader import HostLoader
from cloudsim.metrics.metrics import MetricsCollector
from cloudsim.vms.vm_loader import VMLoader


class CloudSimulation:
    """High-level interface for running a PyCloudSim simulation."""

    def __init__(
        self,
        simulation: Simulation,
        datacenter: Datacenter,
        broker: DatacenterBroker,
        hosts: list,
        vms: list,
        cloudlets: list,
    ) -> None:
        self.simulation = simulation
        self.datacenter = datacenter
        self.broker = broker
        self.hosts = hosts
        self.vms = vms
        self.cloudlets = cloudlets
        self.collector = MetricsCollector()

    @classmethod
    def from_files(
        cls,
        hosts: str | Path,
        vms: str | Path,
        cloudlets: str | Path,
        scheduler,
    ) -> "CloudSimulation":
        """Create a simulation from JSON dataset files."""

        simulation = Simulation()

        hosts_data = HostLoader.load(str(hosts))

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
            hosts=hosts_data,
            characteristics=characteristics,
            scheduling_interval=DEFAULT_SCHEDULING_INTERVAL,
        )

        simulation.add_entity(datacenter)

        broker = DatacenterBroker(
            name="Broker-1",
            scheduler=scheduler,
        )

        simulation.add_entity(broker)
        broker.add_datacenter(datacenter)

        vms_data = VMLoader.load(str(vms))
        broker.submit_vm_list(vms_data)

        cloudlets_data = TaskLoader.load(str(cloudlets))
        broker.submit_cloudlet_list(cloudlets_data)

        return cls(
            simulation=simulation,
            datacenter=datacenter,
            broker=broker,
            hosts=hosts_data,
            vms=vms_data,
            cloudlets=cloudlets_data,
        )

    def run(self):
        """Run the simulation and return calculated metrics."""

        self.simulation.run()

        return self.collector.compute(
            cloudlets=self.cloudlets,
            vms=self.vms,
            datacenter=self.datacenter,
            sim_end_time=self.simulation.clock.now(),
        )