import random
import json
from typing import List

class GenerateCloudlets:
    def __init__(self, count: int):
        self.count = count

    def generate(self) -> List[dict]:
        cloudlets = []
        for i in range(self.count):
            cloudlets.append({
                "id": i,
                "length": random.randint(50000, 100000),
                "pes": random.randint(1, 4),
                "file_size": random.randint(100, 1000),
                "output_size": random.randint(100, 1000),
                "arrival_time": random.randint(0, 0),
                "priority": random.randint(0, 5),
            })
        return cloudlets

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.generate(), f)   

if __name__ == "__main__":
    generate_cloudlets = GenerateCloudlets(count=75)
    generate_cloudlets.save("cloudlets_75.json")