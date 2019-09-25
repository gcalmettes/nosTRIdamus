import mysql.connector
import pandas as pd
from sklearn.pipeline import Pipeline

from config import Cfg as cfg

from transformers import ComputeRaceRouteFeatures, ComputeRaceHistoryStats,\
    KeepActiveRacesOnly, RemoveDuplicates, CleanUpNames, AddCountryCode,\
    FillMissingRegions, ExtractMonth, GetLatestDateAndLocation, SelectColumns,\
    HasIronKids, RaceAttractivity, FractionOfHomeCountryRacer,\
    FractionOfHomeRegionRacer, FemaleRatio, WorldChampionshipSlots,\
    DistanceToNearestShoreline, DistanceToNearestAirport, GetNearbyFacilities,\
    GetTypicalWeather, GetTypicalTemperatures, RacingTimesStatistics,\
    RunElevationMap, BikeElevationMap, IsHalf


# Load data from db
cnx = mysql.connector.connect(
  user=cfg.mysql_user, database=cfg.mysql_db,
  password=cfg.mysql_pw, ssl_disabled=True)

query = "SELECT * FROM races;"
# execute the query and assign it to a pandas dataframe
df_races = pd.read_sql(query, con=cnx)

cnx.close()


preprocessor = Pipeline([
    ("keep active races", KeepActiveRacesOnly()),
    ("remove duplicates", RemoveDuplicates()),
    ("format name", CleanUpNames()),
    ("add country code", AddCountryCode()),
    ("fill missing world regions", FillMissingRegions()),
    ("extract month from date", ExtractMonth()),
    ("update date and location", GetLatestDateAndLocation()),
    ("extract history statistics", ComputeRaceHistoryStats()),
    ("compute races geo features", ComputeRaceRouteFeatures()),
    ("extract ironKids race information", HasIronKids()),
    ("compute race attractivity coefficient", RaceAttractivity()),
    ("compute percentage of racers from country", FractionOfHomeCountryRacer()),
    ("compute percentage of racers from world region", FractionOfHomeRegionRacer()),
    ("compute percentage of females", FemaleRatio()),
    ("get world championship qualifyers", WorldChampionshipSlots()),
    ("calculate distance to nearest shoreline", DistanceToNearestShoreline()),
    ("calculate distance to_nearest airport", DistanceToNearestAirport()),
    ("get touristic facilities nearby", GetNearbyFacilities()),
    ("get typical weather", GetTypicalWeather()),
    ("get typical temperatures", GetTypicalTemperatures()),
    ("compute race times statistics", RacingTimesStatistics()),
    ("get run profile", RunElevationMap()),
    ("get bike profile", BikeElevationMap()),
    ("extract race type (70.3/full) information", IsHalf()),
    ("select only relevant columns", SelectColumns())
])

transformed_races = preprocessor.fit_transform(df_races)

# save to flask app
transformed_races.to_csv("./../flask_app/nostrappdamus/model/data/races_features.csv", index=False)

# save final
transformed_races.to_csv("./../data/clean/races_features.csv", index=False)

print('Race pipeline successfully run!')
