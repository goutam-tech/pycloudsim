"""
Genetic Algorithm (GA) Cloudlet Scheduler.

Schedules cloudlets onto virtual machines using a Genetic Algorithm.
Each chromosome represents a mapping of cloudlets to VMs. The GA
evolves the population using selection, crossover, and mutation
to minimize the overall makespan.
"""

from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING

from cloudsim.schedulers.schedulers import CloudletScheduler
from cloudsim.core.constants import CloudletState

if TYPE_CHECKING:
    from cloudsim.cloudlets.cloudlet import Cloudlet
    from cloudsim.vms.vm import VM


class GAScheduler(CloudletScheduler):
    """
    Genetic Algorithm cloudlet scheduler.

    Chromosome:
        gene[i] = VM index assigned to cloudlet i

    Fitness:
        Makespan (maximum VM completion time)

    Lower fitness is better.
    """

    def __init__(
        self,
        population_size: int = 30,
        generations: int = 50,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        seed: int = 42,
    ) -> None:
        """Initialize the Genetic Algorithm scheduler."""

        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

        self.random = random.Random(seed)
        self._cloudlets: List["Cloudlet"] = []

    def submit_cloudlets(self, cloudlets: List["Cloudlet"], vms: List["VM"]) -> None:
        """
        Schedule cloudlets using a Genetic Algorithm.

        Args:
            cloudlets: List of cloudlets.
            vms: List of available VMs.

        Raises:
            ValueError: If no VMs exist.
        """

        if not vms:
            raise ValueError("GAScheduler requires at least one VM.")

        chromosome_length = len(cloudlets)

        # -------------------------------------------------------
        # Initial population
        # -------------------------------------------------------

        population = [
            [
                self.random.randrange(len(vms))
                for _ in range(chromosome_length)
            ]
            for _ in range(self.population_size)
        ]

        # -------------------------------------------------------
        # Fitness Function
        # -------------------------------------------------------

        def fitness(chromosome):

            vm_times = [0.0] * len(vms)

            for gene, cloudlet in zip(chromosome, cloudlets):
                vm = vms[gene]
                vm_times[gene] += cloudlet.length / vm.mips

            return max(vm_times)

        # -------------------------------------------------------
        # Tournament Selection
        # -------------------------------------------------------

        def selection():

            a = self.random.choice(population)
            b = self.random.choice(population)

            return a if fitness(a) < fitness(b) else b

        # -------------------------------------------------------
        # Single-point crossover
        # -------------------------------------------------------

        def crossover(parent1, parent2):

            if self.random.random() > self.crossover_rate:
                return parent1[:], parent2[:]

            point = self.random.randint(1, chromosome_length - 1)

            child1 = parent1[:point] + parent2[point:]
            child2 = parent2[:point] + parent1[point:]

            return child1, child2

        # -------------------------------------------------------
        # Mutation
        # -------------------------------------------------------

        def mutate(chromosome):

            for i in range(chromosome_length):

                if self.random.random() < self.mutation_rate:
                    chromosome[i] = self.random.randrange(len(vms))

        # -------------------------------------------------------
        # Evolution
        # -------------------------------------------------------

        for _ in range(self.generations):

            new_population = []

            while len(new_population) < self.population_size:

                parent1 = selection()
                parent2 = selection()

                child1, child2 = crossover(parent1, parent2)

                mutate(child1)
                mutate(child2)

                new_population.append(child1)

                if len(new_population) < self.population_size:
                    new_population.append(child2)

            population = new_population

        # -------------------------------------------------------
        # Best chromosome
        # -------------------------------------------------------

        best = min(population, key=fitness)

        # -------------------------------------------------------
        # Assign cloudlets
        # -------------------------------------------------------

        for cloudlet, vm_index in zip(cloudlets, best):

            vm = vms[vm_index]

            cloudlet.assigned_vm_id = vm.vm_id
            cloudlet.state = CloudletState.QUEUED

            vm.cloudlets.append(cloudlet)
            self._cloudlets.append(cloudlet)

    def get_next_cloudlet(self) -> Optional["Cloudlet"]:
        """Return the next queued or executing cloudlet."""

        for cl in self._cloudlets:
            if cl.state in (
                CloudletState.QUEUED,
                CloudletState.INEXEC,
            ):
                return cl

        return None

    def is_finished(self) -> bool:
        """Return True when all submitted cloudlets have completed."""

        return all(
            cl.state == CloudletState.SUCCESS
            for cl in self._cloudlets
        )

    def reset(self) -> None:
        """Reset scheduler state."""

        self._cloudlets.clear()