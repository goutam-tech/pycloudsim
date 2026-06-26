"""
PyCloudSim Constants Module.

Defines global constants used across the simulation framework.
"""

# Event Types
class EventType:
    """Enumeration of simulation event types."""
    VM_CREATE = "VM_CREATE"
    VM_DESTROY = "VM_DESTROY"
    CLOUDLET_SUBMIT = "CLOUDLET_SUBMIT"
    CLOUDLET_COMPLETE = "CLOUDLET_COMPLETE"
    HOST_FAILURE = "HOST_FAILURE"
    SIMULATION_END = "SIMULATION_END"
    DATACENTER_REGISTER = "DATACENTER_REGISTER"
    VM_MIGRATE = "VM_MIGRATE"


# Simulation defaults
DEFAULT_SCHEDULING_INTERVAL: float = 0.1
DEFAULT_BANDWIDTH: float = 10000.0  # Mbps
DEFAULT_STORAGE: float = 100000.0   # MB
DEFAULT_COST_PER_SECOND: float = 0.01
DEFAULT_COST_PER_MEM: float = 0.05
DEFAULT_COST_PER_STORAGE: float = 0.001
DEFAULT_COST_PER_BW: float = 0.001

# Power constants
IDLE_POWER: float = 100.0    # Watts
MAX_POWER: float = 250.0     # Watts

# SLA thresholds
SLA_CPU_THRESHOLD: float = 0.90      # 90%
SLA_RAM_THRESHOLD: float = 0.95      # 95%
SLA_RESPONSE_TIME_THRESHOLD: float = 10.0  # seconds

# Cloudlet states
class CloudletState:
    """Cloudlet execution states."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    INEXEC = "INEXEC"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


# VM states
class VMState:
    """VM lifecycle states."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    MIGRATING = "MIGRATING"
    DESTROYED = "DESTROYED"
