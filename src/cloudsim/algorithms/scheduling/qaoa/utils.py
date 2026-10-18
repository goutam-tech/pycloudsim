"""
QAOA Scheduler Utilities.

Contains utility functions for mapping qubit indices, validating inputs,
and calculating scheduling-specific cost metrics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


def get_qubit_index(cloudlet_idx: int, vm_idx: int, num_vms: int) -> int:
    """
    Map a 2D (cloudlet, VM) index to a 1D qubit index.

    Args:
        cloudlet_idx: Index of the cloudlet in the batch.
        vm_idx: Index of the VM in the VM list.
        num_vms: Total number of VMs.

    Returns:
        The 1D qubit index.
    """
    return cloudlet_idx * num_vms + vm_idx


def get_cloudlet_vm_indices(qubit_idx: int, num_vms: int) -> tuple[int, int]:
    """
    Map a 1D qubit index back to a 2D (cloudlet, VM) index.

    Args:
        qubit_idx: The 1D qubit index.
        num_vms: Total number of VMs.

    Returns:
        A tuple of (cloudlet_index, vm_index).
    """
    return qubit_idx // num_vms, qubit_idx % num_vms


def compute_schedule_metrics(
    assignment: Dict[int, int],
    cloudlets: List["Cloudlet"],
    vms: List["VM"],
) -> Dict[str, float]:
    """
    Compute scheduling performance metrics for a given assignment mapping.

    Args:
        assignment: A dictionary mapping cloudlet index to VM index.
        cloudlets: List of cloudlets scheduled.
        vms: List of available VMs.

    Returns:
        A dictionary containing:
            - makespan: Maximum execution time on any VM.
            - avg_waiting_time: Average waiting time of cloudlets.
            - load_balance_index: Standard deviation of VM workloads.
    """
    if not assignment or not cloudlets or not vms:
        return {"makespan": 0.0, "avg_waiting_time": 0.0, "load_balance_index": 0.0}

    vm_times = [0.0] * len(vms)
    vm_cloudlets: Dict[int, List["Cloudlet"]] = {j: [] for j in range(len(vms))}

    # Group cloudlets by VM
    for cl_idx, vm_idx in assignment.items():
        if vm_idx < len(vms):
            cl = cloudlets[cl_idx]
            vm = vms[vm_idx]
            exec_time = cl.length / vm.total_mips if vm.total_mips > 0 else 0.0
            vm_times[vm_idx] += exec_time
            vm_cloudlets[vm_idx].append(cl)

    # Makespan
    makespan = max(vm_times)

    # Average Waiting Time (using sequential queueing on each VM)
    total_waiting_time = 0.0
    for j, cls in vm_cloudlets.items():
        if not cls:
            continue
        # Sort by arrival or keep the default order
        vm = vms[j]
        current_wait = 0.0
        for cl in cls:
            total_waiting_time += current_wait
            current_wait += cl.length / vm.total_mips if vm.total_mips > 0 else 0.0

    avg_waiting_time = total_waiting_time / len(cloudlets)

    # Load Balance Index (SD or variance of VM times)
    mean_time = sum(vm_times) / len(vms)
    variance = sum((t - mean_time) ** 2 for t in vm_times) / len(vms)
    load_balance_index = variance ** 0.5

    return {
        "makespan": makespan,
        "avg_waiting_time": avg_waiting_time,
        "load_balance_index": load_balance_index,
    }
