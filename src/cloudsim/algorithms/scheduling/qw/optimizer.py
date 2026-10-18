"""
Classical Optimizer Registry for Quantum Walk Scheduler.

Sets up and retrieves optimization algorithms from qiskit_algorithms.optimizers.
"""

from __future__ import annotations

from typing import Any
from qiskit_algorithms.optimizers import (
    COBYLA,
    SPSA,
    NELDER_MEAD,
    Optimizer,
)


def get_optimizer(
    name: str,
    maxiter: int = 100,
    **kwargs: Any,
) -> Optimizer:
    """
    Get a configured Qiskit Optimizer instance by name.

    Args:
        name: Name of the optimizer (e.g. 'COBYLA', 'SPSA', 'Nelder-Mead').
        maxiter: Maximum number of classical iterations.
        kwargs: Additional configuration parameters for the optimizer.

    Returns:
        An instance of qiskit_algorithms.optimizers.Optimizer.
    """
    name_clean = name.strip().upper().replace("-", "_")

    if name_clean == "COBYLA":
        return COBYLA(maxiter=maxiter, **kwargs)
    elif name_clean == "SPSA":
        return SPSA(maxiter=maxiter, **kwargs)
    elif name_clean == "NELDER_MEAD":
        return NELDER_MEAD(maxiter=maxiter, **kwargs)
    else:
        return COBYLA(maxiter=maxiter, **kwargs)
