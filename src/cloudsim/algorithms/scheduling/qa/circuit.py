"""
Quantum Annealing Pauli Evolution Circuit Builder.

Constructs parameterized quantum circuits implementing Trotterized
quantum annealing via Pauli evolution. The circuit simulates the
adiabatic time evolution:

    H(s) = (1-s) * H_mixer + s * H_cost

where H_mixer = Σ_i X_i (transverse field) and H_cost is the Ising cost
Hamiltonian. Each Trotter layer applies Pauli rotation gates (RX, RZ, RZZ)
to implement e^{-i * dt * H(s)}.
"""

from __future__ import annotations

from qiskit.circuit import ParameterVector, QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


def build_qa_circuit(
    num_qubits: int,
    cost_operator: SparsePauliOp,
    reps: int = 1,
    measure: bool = True,
) -> QuantumCircuit:
    """
    Construct a parameterized Quantum Annealing circuit using Pauli evolution.

    The circuit implements Trotterized adiabatic evolution:
      |+⟩^⊗n → e^{-i*θ₁*H(s₁)} → ... → e^{-i*θ_reps*H(s_reps)} → measure

    where s_k = k/reps is the annealing fraction for layer k, H(s_k) is
    the interpolated Hamiltonian, and θ_k are the variational time-step
    parameters.

    Each Trotter layer decomposes into:
      - RX gates for the transverse-field mixer: e^{-i*θ*(1-s)*X_i}
      - RZ gates for single-qubit cost terms: e^{-i*θ*s*c_i*Z_i}
      - RZZ gates for two-qubit cost terms: e^{-i*θ*s*c_ij*Z_i*Z_j}

    Args:
        num_qubits: Total number of qubits (representing cloudlet-VM variables).
        cost_operator: The cost Hamiltonian SparsePauliOp.
        reps: Number of Trotter layers (p).
        measure: If True, append measurement gates to all qubits.

    Returns:
        A parameterized Qiskit QuantumCircuit.
    """
    qc = QuantumCircuit(num_qubits)

    # 1. Hadamard Initialization (ground state of H_mixer = Σ X_i)
    for qubit in range(num_qubits):
        qc.h(qubit)

    # Declare annealing time-step parameters (one per Trotter layer)
    theta = ParameterVector("θ", reps)

    # Convert the cost operator to list representation
    terms = cost_operator.to_list()

    # 2. Construct Trotterized annealing layers
    for layer in range(reps):
        # Annealing fraction at this layer: s = (layer + 1) / reps
        # Starts closer to mixer, ends closer to cost
        s = (layer + 1) / reps

        # 2a. Mixer evolution: e^{-i * theta * (1-s) * H_mixer}
        #     H_mixer = Σ X_i  →  e^{-i * θ * (1-s) * X_i} = RX(2 * θ * (1-s))
        for qubit in range(num_qubits):
            qc.rx(2.0 * theta[layer] * (1.0 - s), qubit)

        # 2b. Cost evolution: e^{-i * theta * s * H_cost}
        #     Decompose H_cost into single-Z and ZZ terms
        for pauli_str, coeff in terms:
            coeff_val = coeff.real
            if abs(coeff_val) < 1e-9:
                continue

            z_indices = []
            for idx, char in enumerate(reversed(pauli_str)):
                if char == "Z":
                    z_indices.append(idx)

            angle = 2.0 * theta[layer] * s * coeff_val

            if len(z_indices) == 1:
                # Single-qubit term: RZ(2 * θ * s * c_i)
                qc.rz(angle, z_indices[0])
            elif len(z_indices) == 2:
                # Two-qubit term: RZZ(2 * θ * s * c_ij)
                qc.rzz(angle, z_indices[0], z_indices[1])

    # 3. Measurement of all qubits (optional)
    if measure:
        qc.measure_all()

    return qc
