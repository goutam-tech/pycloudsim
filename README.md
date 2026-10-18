# PyCloudSim

A Python-native cloud computing simulation framework inspired by Java CloudSim.

PyCloudSim provides a discrete-event simulation environment for modelling and
evaluating cloud infrastructures, resource allocation strategies, scheduling
algorithms, energy-aware policies, and virtual machine management.

---

## Features

- **Discrete-event simulation engine** with a priority-queue event loop
- **Datacenters, Hosts, VMs, and Cloudlets** — the full CloudSim entity hierarchy
- **Pluggable scheduling algorithms** — Round Robin, Min-Min, Genetic Algorithm,
  QAOA, Quantum Walk, Quantum Annealing, and more
- **Metrics collection** — makespan, throughput, utilisation, energy, cost, SLA violations
- **Export** — CSV, JSON, and Matplotlib plots
- **Rich terminal output** — colour-coded logs, metrics tables, validation checks,
  and cloudlet execution tables (themed output like the screenshot)
- **`src` layout** — all library code lives under `src/cloudsim/`

---

## Requirements

- Python 3.10+
- `rich` — terminal output
- `matplotlib` — plot generation
- `pytest` — unit testing

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/goutam-tech/pycloudsim.git
cd pycloudsim

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# 3. Install the library in editable mode
pip install -e .

# 4. (Optional) dev tooling
pip install -e .[dev]
```

---

## Quick Start

```python
from cloudsim import CloudSimulation, print_simulation_summary
from cloudsim.algorithms.scheduling import RoundRobinScheduler, MinMinScheduler

# Build a simulation from JSON dataset files
sim = CloudSimulation.from_files(
    hosts="datasets/hosts/hosts.json",
    vms="datasets/vms/vms.json",
    cloudlets="datasets/cloudlets/cloudlets_100.json",
    scheduler=RoundRobinScheduler(),
)

# Run and collect metrics
import time
wall_start = time.perf_counter()
metrics = sim.run()
wall_elapsed = time.perf_counter() - wall_start

# Themed output (banner + metrics table + validation checks + cloudlet table)
print_simulation_summary(
    metrics=metrics,
    cloudlets=sim.cloudlets,
    vms=sim.vms,
    wall_time=wall_elapsed,
    sim_time=sim.simulation.clock.now(),
    events=sim.simulation.total_events_processed,
)
```

Or use the command line:

```bash
pycloudsim info
pycloudsim version
```

---

## Themed Output

PyCloudSim includes a built-in Rich-powered logger so every simulation run
produces professional, colour-coded terminal output:

```python
from cloudsim import (
    print_banner,
    print_metrics_table,
    print_validation_checks,
    print_cloudlet_table,
    print_simulation_summary,
    info,
    success,
    warning,
    error,
    metric,
    make_progress,
)
```

The `print_simulation_summary()` helper renders everything in one call:
a banner panel, a metrics summary table, validation checks (completion,
per-VM CPU utilisation, SLA violations), and a cloudlet execution table.

---

## Project Structure

```
pycloudsim/
├── src/
│   └── cloudsim/                 # Library package (everything lives here)
│       ├── __init__.py           # Public API exports
│       ├── core/                 # Simulation engine, clock, events, entities
│       ├── simulation/           # High-level CloudSimulation interface
│       ├── cloudlets/            # Cloudlet, TaskLoader
│       ├── vms/                  # VM, VMLoader
│       ├── hosts/                # Host, HostLoader
│       ├── datacenters/          # Datacenter, Broker, DatacenterCharacteristics
│       ├── schedulers/           # CloudletScheduler, VMScheduler, built-in policies
│       ├── algorithms/           # Pluggable scheduling algorithms
│       │   ├── scheduling/       # RoundRobin, MinMin, GA, QAOA, QW, QA, …
│       │   ├── power/
│       │   ├── vm_allocation/
│       │   └── migration/
│       ├── provisioners/         # CPU, RAM, BW provisioners
│       ├── metrics/              # SimulationMetrics, MetricsCollector
│       ├── network/              # Network model
│       ├── utils/                # Rich-powered logger
│       └── cli/                  # Command-line interface
├── tests/                        # pytest unit + integration tests
├── datasets/                     # Sample JSON input files
├── experiments/                  # Example experiment scripts
├── results/                      # Generated CSV, JSON, and plots
├── pyproject.toml                # Packaging + tool configuration
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Runtime dependencies
└── README.md
```

---

## Writing a Custom Algorithm

1. Create a file under `src/cloudsim/algorithms/scheduling/my_algorithm.py`.
2. Subclass `CloudletScheduler` from `cloudsim.schedulers`.
3. Implement `submit_cloudlets`, `get_next_cloudlet`, and `is_finished`.
4. Pass an instance to `CloudSimulation.from_files(..., scheduler=MyAlgorithm())`.

```python
from cloudsim.schedulers import CloudletScheduler

class PriorityScheduler(CloudletScheduler):
    def submit_cloudlets(self, cloudlets, vms):
        sorted_cl = sorted(cloudlets, key=lambda c: c.priority)
        for idx, cl in enumerate(sorted_cl):
            cl.assigned_vm_id = vms[idx % len(vms)].vm_id
            cl.state = "QUEUED"
            ...
```

---

## Exported Results

After running an experiment, results are written to:

| Path                        | Contents                              |
|-----------------------------|---------------------------------------|
| `results/csv/cloudlets.csv` | Per-cloudlet timing metrics           |
| `results/csv/summary.csv`   | Aggregated metrics                    |
| `results/json/cloudlets.json` | Per-cloudlet results in JSON        |
| `results/json/summary.json` | Aggregated metrics in JSON           |
| `results/plots/exec_time_hist.png` | Execution time distribution  |
| `results/plots/vm_load.png` | Cloudlet distribution per VM         |
| `results/plots/gantt.png`   | Cloudlet execution timeline (Gantt)  |

---

## Running Tests

```bash
pytest tests/ -v --tb=short
pytest tests/ --cov=cloudsim --cov-report=term-missing
```

---

## License

MIT License.
