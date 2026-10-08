from __future__ import annotations

import json
from typing import List

from cloudsim.cloudlets.cloudlet import Cloudlet


class TaskLoader:

    @staticmethod
    def load(path: str) -> List[Cloudlet]:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cloudlets = []

        for item in data:
            cloudlets.append(
                Cloudlet(
                    cloudlet_id=item["id"],
                    length=item["length"],
                    pes=item["pes"],
                    file_size=item["file_size"],
                    output_size=item["output_size"],
                    arrival_time=item.get("arrival_time", 0.0),
                    priority=item.get("priority", 0),
                    deadline=item.get("deadline")
                )
            )

        return cloudlets