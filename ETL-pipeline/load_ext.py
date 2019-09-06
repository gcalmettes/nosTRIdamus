import json
from dataclasses import dataclass


@dataclass
class RacesDescription:
    url = "./../data/races/races-description.jl"

    def load(self):
        descriptions = {}
        with open(self.url) as f:
            for line in f.readlines():
                data = json.loads(line.strip())
                if (data.get('id', "TBD") != "TBD"):
                    descriptions[data['id']] = data
                else:
                    descriptions[f"TBD_{data['name']}"] = data
        return descriptions
