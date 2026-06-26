"""
PyCloudSim Task Generator Module.

Provides utilities for generating synthetic Cloudlet workloads for experiments.
"""

from __future__ import annotations
import random
from typing import List, Optional

from cloudsim.cloudlets.cloudlet import Cloudlet


class TaskGenerator:
    """
    Generates synthetic Cloudlet workloads for simulation experiments.

    All parameters accept (min, max) tuples to produce uniformly-distributed
    random values.

    Example:
        >>> gen = TaskGenerator(seed=42)
        >>> cloudlets = gen.generate(count=20)
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Initialize the task generator.

        Args:
            seed: Random seed for reproducible experiments.
        """
        self._rng = random.Random(seed)

    def generate(
        self,
        count: int,
        length_range: tuple[float, float] = (1_000_000, 10_000_000),
        pes_range: tuple[int, int] = (1, 4),
        file_size_range: tuple[float, float] = (100, 1000),
        output_size_range: tuple[float, float] = (100, 1000),
        arrival_time_range: tuple[float, float] = (0.0, 0.0),
        priority_range: tuple[int, int] = (0, 5),
        deadline: Optional[float] = None,
        start_id: int = 0,
    ) -> List[Cloudlet]:
        """
        Generate a list of Cloudlets with randomised parameters.

        Args:
            count:              Number of cloudlets to generate.
            length_range:       (min, max) MI for computational length.
            pes_range:          (min, max) PEs required.
            file_size_range:    (min, max) input file size in bytes.
            output_size_range:  (min, max) output size in bytes.
            arrival_time_range: (min, max) arrival time in simulation seconds.
            priority_range:     (min, max) scheduling priority integers.
            deadline:           Optional deadline applied to all cloudlets.
            start_id:           Starting cloudlet_id value.

        Returns:
            A list of Cloudlet objects.
        """
        cloudlets: List[Cloudlet] = []
        for i in range(count):
            c = Cloudlet(
                cloudlet_id=start_id + i,
                length=self._rng.uniform(*length_range),
                pes=self._rng.randint(*pes_range),
                file_size=self._rng.uniform(*file_size_range),
                output_size=self._rng.uniform(*output_size_range),
                arrival_time=self._rng.uniform(*arrival_time_range),
                priority=self._rng.randint(*priority_range),
                deadline=deadline,
            )
            cloudlets.append(c)
        return cloudlets
