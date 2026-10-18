"""
Bitstring Decoder and Constraint Repair for Quantum Walk Scheduler.

Decodes measurement bitstrings from the quantum circuit into cloudlet-to-VM
assignments and applies conflict resolution heuristics to handle constraint
violations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from algorithms.scheduling.qw.utils import get_qubit_index

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


def decode_bitstring(
    bitstring: str,
    num_cloudlets: int,
    num_vms: int,
) -> Dict[int, List[int]]:
    """
    Decode a raw binary bitstring into a tentative VM assignment list per cloudlet.

    Note: Qiskit measurement bitstrings are ordered right-to-left. Qubit p is at
    index (len(bitstring) - 1 - p).

    Args:
        bitstring: A binary string (e.g. '010010').
        num_cloudlets: Number of cloudlets in the batch.
        num_vms: Number of VMs.

    Returns:
        A dictionary mapping cloudlet index to a list of VM indices assigned to it.
    """
    assignment: Dict[int, List[int]] = {i: [] for i in range(num_cloudlets)}

    for i in range(num_cloudlets):
        for j in range(num_vms):
            p = get_qubit_index(i, j, num_vms)
            bit_idx = len(bitstring) - 1 - p

            if 0 <= bit_idx < len(bitstring) and bitstring[bit_idx] == "1":
                assignment[i].append(j)

    return assignment


def repair_assignment(
    decoded_assignment: Dict[int, List[int]],
    cloudlets: List["Cloudlet"],
    vms: List["VM"],
) -> Dict[int, int]:
    """
    Repair conflicts or empty assignments in a tentative mapping.

    Ensures that every cloudlet is mapped to exactly one VM, while prioritizing
    load balancing and capacity constraints.

    Args:
        decoded_assignment: Tentative mapping from decode_bitstring.
        cloudlets: List of cloudlets.
        vms: List of VMs.

    Returns:
        A mapping of cloudlet index to a single assigned VM index.
    """
    final_assignment: Dict[int, int] = {}
    vm_loads = [0.0] * len(vms)

    for j, vm in enumerate(vms):
        vm_loads[j] = sum(
            c.length / vm.total_mips for c in vm.cloudlets if vm.total_mips > 0.0
        )

    for i, cl in enumerate(cloudlets):
        candidates = decoded_assignment.get(i, [])

        valid_candidates = []
        ram_req = getattr(cl, "ram_required", 512)
        storage_req = getattr(cl, "storage_required", 100)
        bw_req = getattr(cl, "bandwidth_required", 100)

        for j in (candidates if candidates else range(len(vms))):
            vm = vms[j]
            used_ram = sum(getattr(c, "ram_required", 512) for c in vm.cloudlets)
            used_storage = sum(getattr(c, "storage_required", 100) for c in vm.cloudlets)
            used_bw = sum(getattr(c, "bandwidth_required", 100) for c in vm.cloudlets)

            if (
                used_ram + ram_req <= vm.ram
                and used_storage + storage_req <= vm.storage
                and used_bw + bw_req <= vm.bandwidth
            ):
                valid_candidates.append(j)

        if valid_candidates:
            target_vm_idx = min(valid_candidates, key=lambda j: vm_loads[j])
        else:
            target_vm_idx = min(range(len(vms)), key=lambda j: vm_loads[j])

        final_assignment[i] = target_vm_idx
        vm = vms[target_vm_idx]
        exec_time = cl.length / vm.total_mips if vm.total_mips > 0.0 else 0.0
        vm_loads[target_vm_idx] += exec_time

    return final_assignment
