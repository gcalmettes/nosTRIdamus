import json
import pandas as pd
import mysql.connector
from dataclasses import dataclass
from config import Cfg as cfg


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
class IronKidsRacesManualMatched:

    def load(self):
        # manual matches so far
        manual_matches = {
            "Cambridge Fun Run": "eagleman70.3",
            "Warsaw": None,  # new race
            "Les Sables dOlonne": None,  # new race
            "Haugesund Norway": "haugesund",
            "Coeur d Alene Fun Run": "coeurdalene70.3",
            "Westfriesland": None,  # irrelevant, own festival
            "Vitoria-Gasteiz": None,  # new race
            "Dip 'N' Dash Lake Placid": None,  # irrelevant, own festival
            "Subaru Canada Fun Run": "canada",
            # "Sonoma County Builders Santa Rosa Fun Run": "santarosa70.3",
            "Lake Placid 70.3 Fun Run": "lakeplacid70.3",
            "Superfrog Fun Run": "superfrog70.3",
            "Alpharetta": None,  # new race
            "Keiki Dip 'n Dash": None,  # new race
            "Mar del Plata": None,  # new race
            "Clearwater Fun Run": None,  # other festival
            "Galveston Fun Run": None,  # new race and will be for Texas 70.3 commemorative year
            "Dip 'N' Dash Florida": "florida70.3"
        }
        return manual_matches


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


@dataclass
class ResultsDf:
    def __init__(self, current_races=[]):
        self.data = None
        self.current_races = current_races

    def cleanUpData(self, yearThreshold=2019):
        # worldchampionship70.3 and worldchampionship70.3m are the same race
        self.data.loc[self.data.race == "worldchampionship70.3m", 'race'] = 'worldchampionship70.3'
        # keep only results of non discontinued races
        self.data = self.data.loc[self.data['race'].isin(self.current_races)]
        # convert date to datetime
        self.data['date'] = pd.to_datetime(self.data['date'])
        self.data['year'] = self.data['year'].apply(int)

        # keep only results from before yearThreshold since year is running currently
        self.data = self.data.loc[self.data['year'] < yearThreshold]

    def addFeatures(self):
        # add years in sport
        years_in_sport = (self.data
             .groupby('athlete')
             .pipe(lambda g: ((g.date.max() - g.date.min()).astype('timedelta64[Y]')) + 1)  # add 1 so if only one race will be 1 year
             .rename('years_in_sport')
        )

        self.data = self.data.merge(years_in_sport, left_on="athlete", right_on="athlete", how="left")
        self.data['years_in_sport'] = self.data.years_in_sport.astype(int)

    def load(self):
        if self.data is None:
            cnx = mysql.connector.connect(user=cfg.mysql_user, database=cfg.mysql_db,
                                          password=cfg.mysql_pw, ssl_disabled=True)

            query = "SELECT * FROM results;"

            # execute the query and assign it to a pandas dataframe
            self.data = pd.read_sql(query, con=cnx)

            cnx.close()

            self.cleanUpData()
            self.addFeatures()

        return self.data
