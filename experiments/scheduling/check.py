# from cloudsim import CloudSimulation
# from cloudsim.utils.logger import print_banner

# from algorithms.scheduling.round_robin import RoundRobinScheduler


# def main():
#     print_banner("PyCloudSim — Round Robin Experiment")

#     simulation = CloudSimulation.from_files(
#         hosts="datasets/hosts/hosts.json",
#         vms="datasets/vms/vms.json",
#         cloudlets="datasets/cloudlets/cloudlets_25.json",
#         scheduler=RoundRobinScheduler(),
#     )

#     results = simulation.run()

#     results.print_summary()
#     results.print_cloudlets()

#     results.export(
#         csv="results/test.csv",
#         json="results/test.json",
#         plots="results/test",
#     )


# if __name__ == "__main__":
#     main()from __future__ import annotations

# import sys
# from pathlib import Path

# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# sys.path.insert(0, str(PROJECT_ROOT))

# from cloudsim import CloudSimulation
# from algorithms.scheduling.round_robin import RoundRobinScheduler


# def main() -> None:
#     simulation = CloudSimulation.from_files(
#         hosts=PROJECT_ROOT / "datasets" / "hosts" / "hosts.json",
#         vms=PROJECT_ROOT / "datasets" / "vms" / "vms.json",
#         cloudlets=PROJECT_ROOT / "datasets" / "cloudlets" / "cloudlets_25.json",
#         scheduler=RoundRobinScheduler(),
#     )

#     metrics = simulation.run()

#     print("Simulation completed")
#     print(f"Makespan: {metrics.makespan:.4f}s")
#     print(f"Completed: {metrics.completed_cloudlets}")
#     print(f"Total: {metrics.total_cloudlets}")


# if __name__ == "__main__":
#     main()

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from cloudsim import CloudSimulation
from algorithms.scheduling.round_robin import RoundRobinScheduler


def main():
    simulation = CloudSimulation.from_files(
        hosts="datasets/hosts/hosts.json",
        vms="datasets/vms/vms.json",
        cloudlets="datasets/cloudlets/cloudlets_25.json",
        scheduler=RoundRobinScheduler(),
    )

    results = simulation.run()

    results.display()
    results.export(
        csv="results/test.csv",
        json="results/test.json",
        plots="results/test",
    )


if __name__ == "__main__":
    main()