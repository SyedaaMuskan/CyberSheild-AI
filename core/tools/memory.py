import json
import os
from datetime import datetime
from typing import Dict, List, Any


class SecurityMemory:

    def __init__(self,
                 memory_file="data/security_memory.json"):

        self.memory_file = memory_file

        os.makedirs(
            os.path.dirname(memory_file),
            exist_ok=True
        )

        if not os.path.exists(memory_file):
            self._save([])

    def _load(self):

        with open(
            self.memory_file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    def _save(self, data):

        with open(
            self.memory_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

    def store_investigation(
        self,
        finding: Dict[str, Any]
    ):

        memory = self._load()

        finding["timestamp"] = (
            datetime.now()
            .isoformat()
        )

        memory.append(finding)

        self._save(memory)

    def get_similar_patterns(
        self,
        vulnerability_type: str
    ) -> List[Dict]:

        memory = self._load()

        return [
            item
            for item in memory
            if item.get(
                "vulnerability_type"
            ) == vulnerability_type
        ]

    def get_high_risk_history(self):

        memory = self._load()

        return [
            item
            for item in memory
            if item.get("severity")
            in [
                "Critical",
                "High"
            ]
        ]