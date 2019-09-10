import json
from dataclasses import dataclass


@dataclass
class RacesGeoInfo:
    url = "./../data/geo-data/races_geo_info.json"

    def load(self):
        with open(self.url, 'r') as f:
            races_geo_info = json.loads(f.read())
        return races_geo_info


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


@dataclass
class MissingRegions:
    missing_regions = {
        'challengeroth': 'Europe',
        'edinburgh70.3': 'Europe',
        'longhorn70.3': 'North America',
        'loscabos': 'North America',
        'miami70.3': 'North America',
        'pula70.3': "Europe",
        'raleigh70.3': 'North America',
        'st.george': 'North America',
        'syracuse70.3': 'North America',
        'thailand70.3': "Asia"
    }

    def load(self):
        return self.missing_regions


@dataclass
class RacesEntrantsCount:
    url = "./../data/races/races-athletes-count.jl"

    def load(self):
        races_entrants_count = {}
        with open(self.url) as f:
            for line in f.readlines():
                data = json.loads(line.strip())
                if races_entrants_count.get(data['id']):
                    races_entrants_count[data['id']].append({
                        "year": int(data['date'][:4]),
                        "entrants": data['count']
                    })
                else:
                    races_entrants_count[data['id']] = [{
                        "year": int(data['date'][:4]),
                        "entrants": data['count']
                    }]
        return races_entrants_count


@dataclass
class IronKidsRaces:
    url = "./../data/races/ironKids-races.json"

    def load(self):
        ironKids_races = {}
        with open(self.url) as f:
            for line in f.readlines():
                data = json.loads(line.strip())
                ironKids_races[data['name'].strip().replace("IRONKIDS ", "")] = data
        return ironKids_races


@dataclass
class AllRaces:
    url = "./../data/races/races.jl"

    def load(self):
        all_races = {}
        with open(self.url) as f:
            for line in f.readlines():
                data = json.loads(line.strip())
                all_races[data['website'].split('.asp')[0]] = data
        return all_races
