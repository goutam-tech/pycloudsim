from __future__ import annotations

import json
from typing import List

from cloudsim.vms.vm import VM


class VMLoader:

    @staticmethod
    def load(path: str) -> List[VM]:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        vms = []

        for item in data:
            vms.append(
                VM(
                    vm_id=item["id"],
                    broker_id=0,
                    mips=item["mips"],
                    pes=item["pes"],
                    ram=item["ram"],
                    bandwidth=item["bandwidth"],
                    storage=item["storage"]
                )
            )

        return vms