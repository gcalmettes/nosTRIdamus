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
    ("active_races", KeepActiveRacesOnly()),
    ("remove_duplicates", RemoveDuplicates()),
    ("format_name", CleanUpNames()),
    ("add_country_code", AddCountryCode()),
    ("fill_missing_regions", FillMissingRegions()),
    ("extract_month", ExtractMonth()),
    ("update_date_and_location", GetLatestDateAndLocation()),
    ("extract_history_stats", ComputeRaceHistoryStats()),
    ("compute_races_geo_features", ComputeRaceRouteFeatures()),
    ("has_ironKids", HasIronKids()),
    ("race_attractivity", RaceAttractivity()),
    ("percentage_racers_from_country", FractionOfHomeCountryRacer()),
    ("percentage_racers_from_region", FractionOfHomeRegionRacer()),
    ("percentage_of_females", FemaleRatio()),
    ("world_championship_qualifyers", WorldChampionshipSlots()),
    ("calculate_distance_to_nearest_shoreline", DistanceToNearestShoreline()),
    ("get_distance_to_nearest_airport", DistanceToNearestAirport()),
    ("touristicity", GetNearbyFacilities()),
    ("get_typical_weather", GetTypicalWeather()),
    ("get_typical_temperatures", GetTypicalTemperatures()),
    ("compute_times_statistics", RacingTimesStatistics()),
    ("get_run_profile", RunElevationMap()),
    ("get_bike_profile", BikeElevationMap()),
    ("is_half_ironman", IsHalf()),
    ("select_columns", SelectColumns())
])

transformed_races = preprocessor.fit_transform(df_races)

# save to flask app
transformed_races.to_csv("./../flask_app/nostrappdamus/model/data/races_features.csv", index=False)

# save final
transformed_races.to_csv("./../data/clean/races_features.csv", index=False)

print('Race pipeline successfully run!')
