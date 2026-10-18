"""
QAOA Parameterized Quantum Circuit Builder.

Constructs parameterized QAOA quantum circuits containing Hadamard initialization,
Ising cost Hamiltonian unitary layers, transverse-field mixer unitary layers,
and measurements of all qubits.
"""

from __future__ import annotations

from qiskit.circuit import ParameterVector, QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


def build_qaoa_circuit(
    num_qubits: int,
    cost_operator: SparsePauliOp,
    reps: int = 1,
    measure: bool = True,
) -> QuantumCircuit:
    """
    Construct a parameterized QAOA circuit for a given cost Hamiltonian.

    Args:
        num_qubits: Total number of qubits (representing cloudlet-VM variables).
        cost_operator: The cost Hamiltonian SparsePauliOp.
        reps: Number of QAOA layers (p).
        measure: If True, append measurement gates to all qubits.

    Returns:
        A parameterized Qiskit QuantumCircuit.
    """
    qc = QuantumCircuit(num_qubits)

    # 1. Hadamard Initialization
    for qubit in range(num_qubits):
        qc.h(qubit)

    # Declare QAOA parameters
    beta = ParameterVector("β", reps)
    gamma = ParameterVector("γ", reps)

    # Convert the cost operator to list representation
    terms = cost_operator.to_list()

    # 2. Construct QAOA layers
    for layer in range(reps):
        # 2a. Cost Unitary: e^{-i * gamma * H_c}
        for pauli_str, coeff in terms:
            coeff_val = coeff.real
            if abs(coeff_val) < 1e-9:
                continue

            # Identify qubits with non-identity Pauli Z operators
            # Note: Qiskit's Pauli string ordering is right-to-left
            z_indices = []
            for idx, char in enumerate(reversed(pauli_str)):
                if char == "Z":
                    z_indices.append(idx)

            if len(z_indices) == 1:
                # Single-qubit term: e^{-i * gamma * coeff * Z_idx} -> Rz(2 * gamma * coeff, idx)
                qc.rz(2.0 * gamma[layer] * coeff_val, z_indices[0])
            elif len(z_indices) == 2:
                # Two-qubit term: e^{-i * gamma * coeff * Z_i * Z_k} -> Rzz(2 * gamma * coeff, i, k)
                qc.rzz(2.0 * gamma[layer] * coeff_val, z_indices[0], z_indices[1])

        # 2b. Mixer Unitary: e^{-i * beta * H_b} where H_b = Sum_i X_i
        for qubit in range(num_qubits):
            qc.rx(2.0 * beta[layer], qubit)

    # 3. Measurement of all qubits (optional)
    if measure:
        qc.measure_all()

    return qc
