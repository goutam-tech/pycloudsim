"""
QAOA Based Cloudlet Scheduler for PyCloudSim.

Implements a cloudlet scheduler that maps cloudlets to VMs using the
Quantum Approximate Optimization Algorithm (QAOA) via Qiskit.
"""

from __future__ import annotations

import logging
from typing import List, Optional, TYPE_CHECKING, Any

from cloudsim.schedulers.schedulers import CloudletScheduler
from cloudsim.core.constants import CloudletState

from algorithms.scheduling.qaoa.hamiltonian import build_hamiltonian
from algorithms.scheduling.qaoa.decoder import decode_bitstring, repair_assignment
from algorithms.scheduling.qaoa.optimizer import get_optimizer

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM

logger = logging.getLogger(__name__)


class QAOAScheduler(CloudletScheduler):
    """
    QAOA-based cloudlet-to-VM scheduler.

    Constructs a cost Hamiltonian representing makespan, waiting time,
    load balance, and capacity constraints, then uses QAOA to find the
    optimal scheduling assignment.
    """

    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        reps: int = 1,
        batch_size: int = 2,
        optimizer_name: str = "COBYLA",
        max_iterations: int = 50,
        lambda_assign: float = 100.0,
        lambda_cap: float = 50.0,
        lambda_invalid: float = 1000.0,
        sampler: Any = None,
    ) -> None:
        """
        Initialize the QAOA Scheduler.

        Args:
            alpha: Weight for average waiting time.
            beta: Weight for load balancing penalty.
            reps: Number of QAOA layers (p).
            batch_size: Number of cloudlets to optimize in a single QAOA step.
            optimizer_name: Name of classical optimizer (COBYLA, SPSA, Nelder-Mead).
            max_iterations: Max iterations for classical optimizer.
            lambda_assign: Penalty weight for assignment constraints.
            lambda_cap: Penalty weight for capacity constraints.
            lambda_invalid: Penalty weight for single-cloudlet capacity violations.
            sampler: Optional Qiskit sampler primitive (defaults to StatevectorSampler).
        """
        self.alpha = alpha
        self.beta = beta
        self.reps = reps
        self.batch_size = batch_size
        self.optimizer_name = optimizer_name
        self.max_iterations = max_iterations
        self.lambda_assign = lambda_assign
        self.lambda_cap = lambda_cap
        self.lambda_invalid = lambda_invalid

        if sampler is None:
            from qiskit.primitives import StatevectorSampler
            self.sampler = StatevectorSampler()
        else:
            self.sampler = sampler

        self._cloudlets: List["Cloudlet"] = []

    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        """
        Optimize cloudlet assignment to VMs using QAOA.

        Args:
            cloudlets: List of cloudlets to be scheduled.
            vms: List of available virtual machines.

        Raises:
            ValueError: If no virtual machines are provided.
        """
        if not vms:
            raise ValueError("QAOAScheduler requires at least one VM.")

        if not cloudlets:
            return

        # Register all submitted cloudlets
        for cl in cloudlets:
            cl.state = CloudletState.QUEUED
            self._cloudlets.append(cl)

        # Segment cloudlets into smaller batches to keep qubit counts within classical simulation limits
        for start_idx in range(0, len(cloudlets), self.batch_size):
            batch = cloudlets[start_idx : start_idx + self.batch_size]

            # 1. Formulate scheduling QUBO & generate Cost Hamiltonian
            op = build_hamiltonian(
                cloudlets=batch,
                vms=vms,
                alpha=self.alpha,
                beta=self.beta,
                lambda_assign=self.lambda_assign,
                lambda_cap=self.lambda_cap,
                lambda_invalid=self.lambda_invalid,
            )

            # Build custom QAOA ansatz without measurement gates for VQE
            from qiskit_algorithms import SamplingVQE
            from algorithms.scheduling.qaoa.circuit import build_qaoa_circuit

            num_qubits = len(batch) * len(vms)
            ansatz = build_qaoa_circuit(
                num_qubits=num_qubits,
                cost_operator=op,
                reps=self.reps,
                measure=False,
            )

            opt = get_optimizer(self.optimizer_name, maxiter=self.max_iterations)
            vqe = SamplingVQE(
                sampler=self.sampler,
                ansatz=ansatz,
                optimizer=opt,
            )

            bitstring = ""
            # 2. Run classical optimizer to minimize Hamiltonian expectation value
            try:
                result = vqe.compute_minimum_eigenvalue(op)

                # 3. Read qubits & decode the bitstring
                best_measurement = result.best_measurement
                if best_measurement is not None and "bitstring" in best_measurement:
                    bitstring = best_measurement["bitstring"]
            except Exception as exc:
                logger.error(
                    "QAOA VQE optimization failed. Falling back to default: %s", exc
                )

            # If optimization failed or returned no result, use a fallback bitstring
            if not bitstring:
                bitstring = "0" * (len(batch) * len(vms))

            # 4. Decode the bitstring into cloudlet-VM assignments
            decoded = decode_bitstring(bitstring, len(batch), len(vms))

            # 5. Apply conflict resolution/repair heuristic
            batch_assignment = repair_assignment(decoded, batch, vms)

            # 6. Allocate resources and assign VMs
            for i, cl in enumerate(batch):
                vm_idx = batch_assignment[i]
                vm = vms[vm_idx]

                cl.assigned_vm_id = vm.vm_id
                cl.state = CloudletState.QUEUED
                vm.cloudlets.append(cl)

    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        """Get the next queued or executing cloudlet."""
        for cl in self._cloudlets:
            if cl.state in (CloudletState.QUEUED, CloudletState.INEXEC):
                return cl
        return None

    def is_finished(self) -> bool:
        """Check if all submitted cloudlets have completed execution."""
        return all(cl.state == CloudletState.SUCCESS for cl in self._cloudlets)

    def reset(self) -> None:
        """Reset the scheduler state for reuse."""
        self._cloudlets.clear()
