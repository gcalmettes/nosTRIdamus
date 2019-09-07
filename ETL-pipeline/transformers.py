import json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from load_ext import RacesGeoInfo, RacesDescription, MissingRegions, RacesEntrantsCount


class KeepActiveRacesOnly(BaseEstimator, TransformerMixin):
    """
    Filter out inactive races
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.loc[X['info'].dropna().index]


class RemoveDuplicates(BaseEstimator, TransformerMixin):
    """
    worldchampionship70.3 and worldchampionship70.3m are same races
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.loc[X.race != 'worldchampionship70.3']


class CleanUpNames(BaseEstimator, TransformerMixin):
    """
    Some cleanup in the names (apostrophe, etc ...)
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # remove apostrophe in racename
        new_racename = X['racename'].apply(lambda x: x.replace("'", '\u2019'))
        # rename worldchampionship race
        new_race = X['race'].apply(lambda x: x if x != 'worldchampionship70.3m'
                                   else 'worldchampionship70.3')
        changed_cols = ['race', 'racename']
        return pd.concat([
            new_race,
            new_racename,
            X.loc[:, [col for col in X.columns if col not in changed_cols]]
        ], axis=1)


class AddCountryCode(BaseEstimator, TransformerMixin):
    """
    Add country code from geo file
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        races_geo_info = RacesGeoInfo().load()

        country_codes = (
            X['race']
                .apply(lambda x: races_geo_info[x]['components']['ISO_3166-1_alpha-3'])
                .rename('country_code')
        )
        return pd.concat([X, country_codes], axis=1)


class ExtractMonth(BaseEstimator, TransformerMixin):
    """
    Extract month from date
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return pd.concat([X, X['date'].apply(lambda x: x.month).rename('month')],
                         axis=1)


class FillMissingRegions(BaseEstimator, TransformerMixin):
    """
    Fill in missing geo regions for specific races
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        missing_regions = MissingRegions().load()

        return pd.concat([
            X.loc[:, [col for col in X.columns if col != 'region']],
            X[['race', 'region']].transpose().apply(
                lambda x: missing_regions[x['race']] if x['race'] in missing_regions else x['region']
            ).rename('region')
        ], axis=1)


class GetLatestDateAndLocation(BaseEstimator, TransformerMixin):
    """
    Ensure date and location are the latest available for each race
    """

    @staticmethod
    def getDateAndLocation(race, date, month, city, descriptions):
        to_check = descriptions.get(race, False)
        if not to_check:
            # maybe need lowercase
            to_check = descriptions.get(race.lower(), False)
        new_date = to_check['date'] if to_check is not False else date if date else ''
        if type(new_date) == str and 'TBD' in new_date:
            new_date = f"TBD {month:02}-{new_date.split('TBD ')[1]}"
        return pd.Series({
            'date': new_date,
            'month': int(new_date.split('-')[1]) if type(new_date) == str and 'TBD' not in new_date and new_date != '' else month,
            'city': to_check['location'] if to_check is not False else city
        })

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # make sure to have latest date and location from latest download
        descriptions = RacesDescription().load()

        return pd.concat([
            X.transpose()
                .apply(lambda x: self.getDateAndLocation(x['race'], x['date'], x['month'], x['city'], descriptions))
                .transpose(),
            X.loc[:, [col for col in X.columns if col not in ['date', 'city', 'month']]]
        ], axis=1)


class SelectColumns(BaseEstimator, TransformerMixin):
    """
    Select columns of interest
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        columns_to_keep = [
            'race', 'racename', 'date', 'month', 'imlink', 'city', 'image_url',
            'logo_url', 'region', 'images', 'country_code', 'lat', 'lon',
            'n_years_existance', 'entrants_count_avg', 'run_sinusoity',
            'run_distance', 'run_elevationGain', 'run_score', 'bike_sinusoity',
            'bike_distance', 'bike_elevationGain', 'bike_score', 'swim_distance',
            'swim_type'
            # 'ironkids_race', 'attractivity_score',
            # 'perc_entrants_from_country', 'perc_entrants_from_region',
            # 'perc_female', 'wc_slots', 'distance_to_nearest_shoreline',
            # 'distance_to_nearest_airport',
            # 'distance_to_nearest_airport_international', 'n_metropolitan_cities',
            # 'n_hotels', 'n_restaurants', 'n_entertainment', 'n_nightlife',
            # 'n_shops', 'n_bike_shops', 'n_pools', 'n_athletic_centers',
            # 'n_fitness_centers', 'weather_icon', 'weather_summary',
            # 'temperatureMin', 'temperatureMax', 'apparentTemperatureMin',
            # 'apparentTemperatureMax', 'swim_min', 'swim_mean', 'swim_max',
            # 'bike_min', 'bike_mean', 'bike_max', 'run_min', 'run_mean', 'run_max',
            # 'run_elevation_map', 'bike_elevation_map', 'is_70.3'
        ]
        return X.loc[:, columns_to_keep]


class ComputeRaceHistoryStats(BaseEstimator, TransformerMixin):
    """
    Some statistics based on past race results
    """
    year_threshold = 2014

    def get_race_participation(self, race, races_entrants_count):
        mean_count = 0
        n_years_existance = 0
        race_participation = races_entrants_count.get(race, 0)
        if not race_participation:
            # try with lowercase
            race_participation = races_entrants_count.get(race.lower(), 0)
        if race_participation:
            counts = np.array([y['entrants'] if y['year'] > self.year_threshold
                               else np.nan for y in race_participation])
            mean_count = np.nanmean(counts)
            n_years_existance = len(race_participation)

        # nan if no results
        mean_count = np.nan if not mean_count else mean_count
        n_years_existance = np.nan if not n_years_existance else n_years_existance

        return pd.Series({
            'n_years_existance': n_years_existance,
            'entrants_count_avg': mean_count
        })

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        races_entrants_count = RacesEntrantsCount().load()

        return pd.concat([
            X,
            X.transpose()
             .apply(lambda x: self.get_race_participation(x['race'], races_entrants_count))
             .transpose()
        ], axis=1)


class ComputeRaceRouteFeatures(BaseEstimator, TransformerMixin):
    """
    Extract info from GPS tracks and co
    """

    # hash for swim type in db
    swim_type = {
        'h': 'harbor',
        'o': 'ocean',
        'l': 'lake',
        'r': 'river'
    }

    @staticmethod
    def get_angle_between(v1, v2, degrees=False):
        angle = np.math.atan2(np.linalg.det([v1, v2]), np.dot(v1, v2))
        if degrees:
            angle = np.degrees(angle)
        return angle

    def get_successive_angles(self, x, y):
        x_diff = x[1:] - x[:-1]
        y_diff = y[1:] - y[:-1]
        angles = []
        for i in range(len(x_diff) - 1):
            v1 = [x_diff[i], y_diff[i]]
            v2 = [x_diff[i + 1], y_diff[i + 1]]
            angles.append(np.abs(self.get_angle_between(v1, v2, degrees=True)))
        return np.array(angles)

    def extract_geo_info(self, race_map, race_info):
        # get lat/lon by averaging run points
        run_map = json.loads(race_map)['run']
        run_data = np.array(run_map['points'])
        lon = run_data[:, 0].mean()
        lat = run_data[:, 1].mean()

        # sinusoity of run route
        run_sinusoity = self.get_successive_angles(run_data[:, 0], run_data[:, 1]).mean()

        # sinusoity of bike route
        bike_map = json.loads(race_map)['bike']
        bike_data = np.array(bike_map['points'])
        bike_sinusoity = self.get_successive_angles(bike_data[:, 0], bike_data[:, 1]).mean()

        # infos
        infos = json.loads(race_info)

        return pd.Series({
            'lat': lat,
            'lon': lon,
            'run_sinusoity': run_sinusoity,
            'run_distance': infos['run']['distance'],
            'run_elevationGain': infos['run']['elevationGain'],
            'run_score': infos['run']['score'],
            'bike_sinusoity': bike_sinusoity,
            'bike_distance': infos['bike']['distance'],
            'bike_elevationGain': infos['bike']['elevationGain'],
            'bike_score': infos['bike']['score'],
            'swim_distance': infos['swim']['distance'],
            'swim_type': self.swim_type[infos['swim']['type']]
        })

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return pd.concat([
            X,
            X.transpose()
             .apply(lambda x: self.extract_geo_info(x['map'], x['info']))
             .transpose()
        ], axis=1)