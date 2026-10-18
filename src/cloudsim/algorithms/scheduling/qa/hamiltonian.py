"""
Ising Hamiltonian Builder for Cloudlet Scheduling.

Formulates the scheduling optimization problem as a Quadratic Unconstrained
Binary Optimization (QUBO) problem and converts it into an Ising Hamiltonian
represented by a Qiskit SparsePauliOp.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Tuple
from qiskit.quantum_info import SparsePauliOp

from algorithms.scheduling.qa.utils import get_qubit_index

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


def build_hamiltonian(
    cloudlets: List["Cloudlet"],
    vms: List["VM"],
    alpha: float = 0.5,
    beta: float = 0.5,
    lambda_assign: float = 100.0,
    lambda_cap: float = 50.0,
    lambda_invalid: float = 1000.0,
) -> SparsePauliOp:
    """
    Build the Ising Hamiltonian operator for scheduling a batch of cloudlets.

    Args:
        cloudlets: List of cloudlets to schedule.
        vms: List of available virtual machines.
        alpha: Weight for average waiting time minimization.
        beta: Weight for load balancing penalty.
        lambda_assign: Penalty weight for the assignment constraint.
        lambda_cap: Penalty weight for VM capacity constraints.
        lambda_invalid: Linear penalty for assignments exceeding single-VM capacity.

    Returns:
        A Qiskit SparsePauliOp representing the cost Hamiltonian.
    """
    n = len(cloudlets)
    m = len(vms)
    q = n * m

    linear = [0.0] * q
    quadratic: Dict[Tuple[int, int], float] = {}

    # ------------------------------------------------------------------
    # 1. Assignment Constraints
    # ------------------------------------------------------------------
    for i in range(n):
        for j in range(m):
            p = get_qubit_index(i, j, m)
            linear[p] -= lambda_assign

            for k in range(j + 1, m):
                r = get_qubit_index(i, k, m)
                quadratic[(p, r)] = quadratic.get((p, r), 0.0) + 2.0 * lambda_assign

    # ------------------------------------------------------------------
    # 2. Makespan and Load Balance
    # ------------------------------------------------------------------
    preloads = [0.0] * m
    current_batch_ids = {cl.cloudlet_id for cl in cloudlets}

    for j, vm in enumerate(vms):
        p_j = vm.total_mips if vm.total_mips > 0.0 else 1.0
        preload_len = sum(
            c.length for c in vm.cloudlets if c.cloudlet_id not in current_batch_ids
        )
        preloads[j] = preload_len / p_j

    s_pre = sum(preloads)

    factor1 = 1.0 + beta
    for j, vm in enumerate(vms):
        p_j = vm.total_mips if vm.total_mips > 0.0 else 1.0
        preload_j = preloads[j]

        for i in range(n):
            cl = cloudlets[i]
            l_i = cl.length
            p = get_qubit_index(i, j, m)

            linear[p] += factor1 * (2.0 * preload_j * l_i / p_j + (l_i ** 2) / (p_j ** 2))

            for k in range(i + 1, n):
                cl_k = cloudlets[k]
                l_k = cl_k.length
                r = get_qubit_index(k, j, m)

                quad_val = factor1 * (2.0 * l_i * l_k / (p_j ** 2))
                quadratic[(p, r)] = quadratic.get((p, r), 0.0) + quad_val

    factor2 = -beta / m
    for i in range(n):
        cl_i = cloudlets[i]
        l_i = cl_i.length

        for j in range(m):
            vm_j = vms[j]
            p_j = vm_j.total_mips if vm_j.total_mips > 0.0 else 1.0
            p = get_qubit_index(i, j, m)

            linear[p] += factor2 * (2.0 * s_pre * l_i / p_j + (l_i ** 2) / (p_j ** 2))

            for k in range(n):
                cl_k = cloudlets[k]
                l_k = cl_k.length
                for l in range(m):
                    vm_l = vms[l]
                    p_l = vm_l.total_mips if vm_l.total_mips > 0.0 else 1.0
                    r = get_qubit_index(k, l, m)

                    if p < r:
                        quad_val = factor2 * (2.0 * l_i * l_k / (p_j * p_l))
                        quadratic[(p, r)] = quadratic.get((p, r), 0.0) + quad_val

    # ------------------------------------------------------------------
    # 3. Average Waiting Time Proxy
    # ------------------------------------------------------------------
    for j, vm in enumerate(vms):
        p_j = vm.total_mips if vm.total_mips > 0.0 else 1.0
        for i in range(n):
            cl_i = cloudlets[i]
            l_i = cl_i.length
            p = get_qubit_index(i, j, m)

            for k in range(i + 1, n):
                cl_k = cloudlets[k]
                l_k = cl_k.length
                r = get_qubit_index(k, j, m)

                quad_val = alpha * (l_i + l_k) / (2.0 * p_j)
                quadratic[(p, r)] = quadratic.get((p, r), 0.0) + quad_val

    # ------------------------------------------------------------------
    # 4. VM Resource Capacity Constraints
    # ------------------------------------------------------------------
    for j, vm in enumerate(vms):
        used_ram = sum(
            getattr(c, "ram_required", 512)
            for c in vm.cloudlets
            if c.cloudlet_id not in current_batch_ids
        )
        used_storage = sum(
            getattr(c, "storage_required", 100)
            for c in vm.cloudlets
            if c.cloudlet_id not in current_batch_ids
        )
        used_bandwidth = sum(
            getattr(c, "bandwidth_required", 100)
            for c in vm.cloudlets
            if c.cloudlet_id not in current_batch_ids
        )

        avail_ram = max(1, vm.ram - used_ram)
        avail_storage = max(1, vm.storage - used_storage)
        avail_bandwidth = max(1, vm.bandwidth - used_bandwidth)

        for i in range(n):
            cl = cloudlets[i]
            ram_req = getattr(cl, "ram_required", 512)
            storage_req = getattr(cl, "storage_required", 100)
            bw_req = getattr(cl, "bandwidth_required", 100)
            p = get_qubit_index(i, j, m)

            if (
                ram_req > avail_ram
                or storage_req > avail_storage
                or bw_req > avail_bandwidth
            ):
                linear[p] += lambda_invalid

            for k in range(i + 1, n):
                cl_k = cloudlets[k]
                ram_req_k = getattr(cl_k, "ram_required", 512)
                storage_req_k = getattr(cl_k, "storage_required", 100)
                bw_req_k = getattr(cl_k, "bandwidth_required", 100)
                r = get_qubit_index(k, j, m)

                ram_penalty = lambda_cap * (ram_req * ram_req_k) / (avail_ram ** 2)
                storage_penalty = lambda_cap * (storage_req * storage_req_k) / (avail_storage ** 2)
                bw_penalty = lambda_cap * (bw_req * bw_req_k) / (avail_bandwidth ** 2)

                quadratic[(p, r)] = (
                    quadratic.get((p, r), 0.0) + ram_penalty + storage_penalty + bw_penalty
                )

    # ------------------------------------------------------------------
    # Convert QUBO to Ising Hamiltonian
    # ------------------------------------------------------------------
    offset = 0.0
    z_coeffs = [0.0] * q
    zz_coeffs: Dict[Tuple[int, int], float] = {}

    for p in range(q):
        val = linear[p]
        offset += 0.5 * val
        z_coeffs[p] -= 0.5 * val

    for (p, r), val in quadratic.items():
        offset += 0.25 * val
        z_coeffs[p] -= 0.25 * val
        z_coeffs[r] -= 0.25 * val
        zz_coeffs[(p, r)] = zz_coeffs.get((p, r), 0.0) + 0.25 * val

    pauli_list = []

    if abs(offset) > 1e-9:
        pauli_list.append(("I" * q, offset))

    for p in range(q):
        if abs(z_coeffs[p]) > 1e-9:
            p_string = ["I"] * q
            p_string[q - 1 - p] = "Z"
            pauli_list.append(("".join(p_string), z_coeffs[p]))

    for (p, r), val in zz_coeffs.items():
        if abs(val) > 1e-9:
            p_string = ["I"] * q
            p_string[q - 1 - p] = "Z"
            p_string[q - 1 - r] = "Z"
            pauli_list.append(("".join(p_string), val))

    if not pauli_list:
        pauli_list.append(("I" * q, 0.0))

    return SparsePauliOp.from_list(pauli_list)
