import json
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


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
        with open("./../data/geo-data/races_geo_info.json", 'r') as f:
            races_geo_info = json.loads(f.read())

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
        return pd.concat([
            X.loc[:, [col for col in X.columns if col != 'region']],
            X[['race', 'region']].transpose().apply(
                lambda x: missing_regions[x['race']] if x['race'] in missing_regions else x['region']
            ).rename('region')
        ], axis=1)
