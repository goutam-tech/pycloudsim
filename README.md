# PyCloudSim

A Python-native cloud computing simulation framework inspired by Java CloudSim.

PyCloudSim provides a discrete-event simulation environment for modelling and
evaluating cloud infrastructures, resource allocation strategies, scheduling
algorithms, energy-aware policies, and virtual machine management.

---

## Features

- **Discrete-event simulation engine** with a priority-queue event loop
- **Datacenters, Hosts, VMs, and Cloudlets** — the full CloudSim entity hierarchy
- **Pluggable scheduling algorithms** — add new algorithms without changing core code
- **Built-in schedulers** — Time Shared and Space Shared policies included
- **Metrics collection** — makespan, throughput, utilisation, energy, cost, SLA violations
- **Export** — CSV, JSON, and Matplotlib plots
- **Rich terminal output** — colour-coded logs and formatted tables

---

## Requirements

- Python 3.10+
- `rich` — terminal output
- `matplotlib` — plot generation
- `pytest` — unit testing

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/pycloudsim.git
cd pycloudsim

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate.bat       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Round Robin experiment
python experiments/scheduling/run_round_robin.py

# 5. Run tests
pytest tests/ -v --tb=short
```

---

## Project Structure

```
pycloudsim/
├── cloudsim/               # Core framework
│   ├── core/               # Simulation engine, clock, events, entities
│   ├── datacenters/        # Datacenter, Broker, DatacenterCharacteristics
│   ├── hosts/              # Host, PowerHost
│   ├── vms/                # VM
│   ├── cloudlets/          # Cloudlet, TaskGenerator
│   ├── schedulers/         # CloudletScheduler, VMScheduler, built-in policies
│   ├── provisioners/       # CPU, RAM, BW provisioners
│   ├── metrics/            # SimulationMetrics, MetricsCollector
│   └── utils/              # Rich-powered logger
├── algorithms/
│   └── scheduling/
│       └── round_robin.py  # Example: Round Robin Scheduler
├── datasets/               # Sample JSON input files
├── experiments/
│   └── scheduling/
│       └── run_round_robin.py   # Main experiment entry point
├── results/                # Generated CSV, JSON, and plots
├── tests/
│   └── test_pycloudsim.py  # Unit + integration tests (pytest)
├── docs/
│   └── PRD.md
├── requirements.txt
├── setup.py
└── README.md
```

---

## Writing a Custom Algorithm

1. Create a file under `algorithms/scheduling/my_algorithm.py`.
2. Subclass `CloudletScheduler` from `cloudsim.schedulers`.
3. Implement `submit_cloudlets`, `get_next_cloudlet`, and `is_finished`.
4. Pass an instance to `DatacenterBroker(scheduler=MyAlgorithm())`.

```python
# algorithms/scheduling/priority_scheduler.py
from cloudsim.schedulers import CloudletScheduler

class PriorityScheduler(CloudletScheduler):
    def submit_cloudlets(self, cloudlets, vms):
        sorted_cl = sorted(cloudlets, key=lambda c: c.priority)
        for idx, cl in enumerate(sorted_cl):
            cl.assigned_vm_id = vms[idx % len(vms)].vm_id
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

## Architecture Overview

```
Experiments
     │
     ▼
Algorithms (RoundRobinScheduler, …)
     │
     ▼
DatacenterBroker
     │
     ▼
Simulation Engine (EventQueue + SimulationClock)
     │
     ▼
Datacenter → Host → VM → Cloudlet
     │
     ▼
MetricsCollector → CSV / JSON / Plots
```

---

## License

MIT License. See `LICENSE` for details.
