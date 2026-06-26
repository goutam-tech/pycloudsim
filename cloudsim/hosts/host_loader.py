from __future__ import annotations

import json
from typing import List

from cloudsim.hosts.host import PowerHost


class HostLoader:

    @staticmethod
    def load(path: str) -> List[PowerHost]:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        hosts = []

        for item in data:
            hosts.append(
                PowerHost(
                    host_id=item["id"],
                    mips=item["mips"],
                    pes=item["pes"],
                    ram=item["ram"],
                    bandwidth=item["bandwidth"],
                    storage=item["storage"],
                    idle_power=item["idle_power"],
                    max_power=item["max_power"]
                )
            )

        return hosts