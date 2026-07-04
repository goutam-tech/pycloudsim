"""
Quantum Walk Parameterized Circuit Builder.

Constructs parameterized quantum circuits implementing a discrete-time
quantum walk on the hypercube graph for solving combinatorial optimization
problems. The walk alternates between cost Hamiltonian phase separation
and Grover diffusion (the quantum walk step on the hypercube).
"""

from __future__ import annotations

from qiskit.circuit import ParameterVector, QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


def build_qw_circuit(
    num_qubits: int,
    cost_operator: SparsePauliOp,
    reps: int = 1,
    measure: bool = True,
) -> QuantumCircuit:
    """
    Construct a parameterized Quantum Walk circuit for a given cost Hamiltonian.

    The circuit implements a discrete-time quantum walk on the hypercube graph:
      |s⟩ -> e^{-iγ₁H_c} -> W -> ... -> e^{-iγ_pH_c} -> W -> measure

    where W = H⊗ⁿ(2|0⟩⟨0| - I)H⊗ⁿ is the Grover diffusion operator (the
    quantum walk step on the hypercube), and H_c is the cost Hamiltonian.

    Args:
        num_qubits: Total number of qubits (representing cloudlet-VM variables).
        cost_operator: The cost Hamiltonian SparsePauliOp.
        reps: Number of Quantum Walk layers (p).
        measure: If True, append measurement gates to all qubits.

    Returns:
        A parameterized Qiskit QuantumCircuit.
    """
    qc = QuantumCircuit(num_qubits)

    # 1. Hadamard Initialization (equal superposition over all basis states)
    for qubit in range(num_qubits):
        qc.h(qubit)

    # Declare Quantum Walk parameters
    gamma = ParameterVector("γ", reps)

    # Convert the cost operator to list representation
    terms = cost_operator.to_list()

    # 2. Construct Quantum Walk layers
    for layer in range(reps):
        # 2a. Cost Unitary: e^{-i * gamma * H_c}
        for pauli_str, coeff in terms:
            coeff_val = coeff.real
            if abs(coeff_val) < 1e-9:
                continue

            z_indices = []
            for idx, char in enumerate(reversed(pauli_str)):
                if char == "Z":
                    z_indices.append(idx)

            if len(z_indices) == 1:
                qc.rz(2.0 * gamma[layer] * coeff_val, z_indices[0])
            elif len(z_indices) == 2:
                qc.rzz(2.0 * gamma[layer] * coeff_val, z_indices[0], z_indices[1])

        # 2b. Quantum Walk Step (Grover diffusion on the hypercube)
        #     W = H⊗ⁿ(2|0⟩⟨0| - I)H⊗ⁿ
        for qubit in range(num_qubits):
            qc.h(qubit)

        for qubit in range(num_qubits):
            qc.x(qubit)

        # Multi-controlled Z: phase flip on |1...1⟩
        if num_qubits == 1:
            qc.z(0)
        elif num_qubits == 2:
            qc.cz(0, 1)
        else:
            qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)
            qc.z(num_qubits - 1)
            qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)

        for qubit in range(num_qubits):
            qc.x(qubit)

        for qubit in range(num_qubits):
            qc.h(qubit)

    # 3. Measurement of all qubits (optional)
    if measure:
        qc.measure_all()

    return qc
