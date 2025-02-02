import json
import re
import numpy as np
from scipy import signal
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from load_ext import RacesGeoInfo, RacesDescription, MissingRegions,\
                     RacesEntrantsCount, IronKidsRaces, AllRaces,\
                     IronKidsRacesManualMatched, ResultsDf, CountryInfo,\
                     CountryISOCodes, CountryISOCodesMiddleEast,\
                     WorldChampionshipQualifyers, Shorelines, Airports,\
                     Hotels, Restaurants, Entertainment, Nightlife,\
                     Shops, BikeShops, Pools, AthleticCenters,\
                     FitnessCenters, MetropolitanArea, Weather


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
        # city of worldchampionship70.3 is messed up
        new_city = X['city'].apply(lambda x: x if x != 'September 1 & 2'
                                   else 'Nelson Mandela Bay, South Africa')
        return X.drop(['race', 'racename', 'city'], axis=1).assign(
            racename=new_racename,
            race=new_race,
            city=new_city
        )


class AddCountryCode(BaseEstimator, TransformerMixin):
    """
    Add country code from geo file
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        races_geo_info = RacesGeoInfo().load()

        country_codes = X['race'].apply(
            lambda x: races_geo_info[x]['components']['ISO_3166-1_alpha-3']
        )

        return X.assign(
            country_code=country_codes
        )


class ExtractMonth(BaseEstimator, TransformerMixin):
    """
    Extract month from date
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.assign(month=X['date'].apply(lambda x: x.month))


class FillMissingRegions(BaseEstimator, TransformerMixin):
    """
    Fill in missing geo regions for specific races
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        missing_regions = MissingRegions().load()

        return X.assign(
            region=(
                X[['race', 'region']]
                .transpose()
                .apply(lambda x: missing_regions[x['race']] if x['race'] in missing_regions else x['region'])
            )
        )


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

        updated_info = (
            X.transpose()
                .apply(lambda x: self.getDateAndLocation(x['race'], x['date'], x['month'], x['city'], descriptions))
                .transpose()
        )

        return X.assign(
            date=updated_info['date'],
            month=updated_info['month'],
            city=updated_info['city']
        )


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


class HasIronKids(BaseEstimator, TransformerMixin):
    """
    Does the race have ironKids race
    """

    @staticmethod
    def getIronKidsRaces():
        return IronKidsRaces().load()

    @staticmethod
    def getAllRaces():
        return AllRaces().load()

    @staticmethod
    def getIronKidsRacesManualMatched():
        return IronKidsRacesManualMatched().load()

    def getMatchedIronKidsRaces(self):
        ironKids_races = self.getIronKidsRaces()
        all_races = self.getAllRaces()

        not_matched = []
        for kidsrace in ironKids_races:
            # try to find a match in all_races dataset
            url = ironKids_races[kidsrace]['url']
            match = 0
            duplicate = 0
            for race in all_races:
                if re.match(race, url):
                    # try first to match parent website
                    ironKids_races[kidsrace]['race_parent'] = all_races[race]['id']
                    match = 1

                if not match:
                    # there is a bunch of Fun Run in races title, try to match name without
                    stripped_name = kidsrace.replace(" Fun Run", "")
                    if stripped_name in all_races[race]['name']:
                        ironKids_races[kidsrace]['race_parent'] = all_races[race]['id']
                        match = 1
                        # get my attention if we match several races
                        duplicate += 1

            if not match:
                not_matched.append(kidsrace)

        return ironKids_races, not_matched

    def getIronKidsParentRaces(self):

        ironKids_races, not_matched = self.getMatchedIronKidsRaces()
        manual_matched = self.getIronKidsRacesManualMatched()

        # add manual matched to dataset
        for kidsrace in manual_matched:
            ironKids_races[kidsrace]['race_parent'] = manual_matched[kidsrace]

        # need to add a note to update manual matches if not all no_matched
        # are not covered by manual_matched

        races_parent = []

        for kidsrace in ironKids_races:
            parent_race = ironKids_races[kidsrace]['race_parent']
            if parent_race:  # some are set to None
                races_parent.append(parent_race)

        return races_parent

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        races_parent = self.getIronKidsParentRaces()

        return X.assign(
            hasIronKids=X['race'].apply(lambda x: 1 if x in races_parent else 0)
        )


class RaceAttractivity(BaseEstimator, TransformerMixin):
    """
    Feature computed based on the behavior of athletes who have the possibility
    of coming back to a race. Do they actually returns?
    """

    def weighted_ratio(self, df, m=None, C=None):
        '''
        Function that computes the weighted ratio of each race
        '''

        m = self.m if m is None else m
        C = self.C if C is None else C
        v = df['total_hits']
        R = df['ratio']

        # Calculation based on the IMDB formula
        return ((v / (v + m) * R) + (m / (m + v) * C))

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_results = ResultsDf(current_races=X['race']).load()

        # keep only athletes that have done more than one season
        # so they had the ability to redo the same race if they wanted
        df_multi_season = df_results.loc[df_results["years_in_sport"] > 1]

        # number of editions of the race
        n_editions = (
            df_multi_season
                .groupby(['race', 'year'])
                .size()
                .reset_index()
                .groupby('race')
                .size()
                .rename("n_edition")
        )

        # how many times races have been raced by those multi-season athletes?
        total_hits = (
            df_multi_season
                .groupby(['race'])
                .size()
                .reset_index()
                .rename(columns={0: "total_hits"})
        )

        # how many times multi-season athletes returned to race again the same race?
        returned_hits = (
            df_multi_season
                .groupby(['race', 'athlete'])
                .size()
                .reset_index()
                .groupby('race')
                .size()
                .rename("returned_hits")
        )

        df_results = (
            total_hits
                .merge(returned_hits, left_on="race", right_on="race", how="left")
                .merge(n_editions, left_on="race", right_on="race", how="left")
        )
        df_results["ratio"] = df_results['returned_hits'] / df_results['total_hits']

        # Only the races with more than 1 editions have potential returning entrants.
        # If returned hits is < than total_hits it means there are entrants with same name

        # keep only races with >1 editions
        select_results = df_results.loc[df_results.n_edition > 1]
        self.C = select_results.ratio.mean()
        self.m = select_results["total_hits"].quantile(0.6)
        select_results["attractivity_score"] = select_results.apply(self.weighted_ratio, axis=1)

        # add back the races with just 1 edition and fill na
        df_results = pd.concat([
            select_results, df_results.loc[df_results.n_edition == 1]
        ], sort=False).fillna(select_results.median())

        return X.merge(df_results[['race', 'attractivity_score']],
                       left_on="race", right_on="race", how="left")


class FractionOfHomeCountryRacer(BaseEstimator, TransformerMixin):
    """
    Compute the percentage of people from country of the race
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_results = ResultsDf(current_races=X['race']).load()

        nationalities = (df_results
            .groupby(['race', 'country'])
            .size()
            .reset_index()
            .rename(columns={0: 'count'})
            .pivot(index='race', columns='country', values='count')

        )

        from_country = pd.DataFrame(list(
            nationalities.index.map(lambda race:
                {'index': race,
                 'from_country': nationalities.loc[race, X.loc[X.race == race, 'country_code'].values[0]]
                }
            )
        ))

        from_country = from_country.set_index('index')

        from_country = pd.concat([
            nationalities.sum(axis=1).rename("total"),
            from_country
        ], axis=1)

        from_country['perc_entrants_from_country'] = from_country['from_country'] / from_country['total']
        from_country['race'] = from_country.index

        return X.merge(from_country[['race', 'perc_entrants_from_country']],
                       left_on="race", right_on="race", how="left")


class FractionOfHomeRegionRacer(BaseEstimator, TransformerMixin):
    """
    Compute the percentage of people from region of the race
    """

    codes = CountryISOCodes().load()
    codes_middle_east = CountryISOCodesMiddleEast().load()
    countries = CountryInfo().load()

    def get_region_from_ISO3(self, ISO3_code, changeOceania=False):
        # get ISO-2 correspondance
        ISO2_code = self.codes.loc[self.codes['alpha3'] == ISO3_code, 'alpha2'].values
        ISO2_code = ISO2_code[0] if len(ISO2_code) else False
        return self.get_region_from_ISO2(ISO2_code, changeOceania)

    def get_region_from_ISO2(self, ISO2_code, changeOceania=False):
        if ISO2_code and ISO2_code not in self.codes_middle_east['alpha2'].tolist():
            country = list(filter(lambda x: x['code'] == ISO2_code, self.countries))
            if len(country):
                region = country[0].get('continent', False)
                if changeOceania and region == "Oceania":
                    # oceania is referred as Australia in races regions
                    region = 'Australia'
                return region
            else:
                return ''
        elif ISO2_code and ISO2_code in self.codes_middle_east['alpha2'].tolist():
            return 'Middle East'
        else:
            return ''

    def get_race_region(self, race, races_df):
        if race:
            region = races_df.loc[races_df.race == race, 'region']
            if len(region) > 0:
                return region.values[0]
            else:
                return 'None'
        else:
            return 'None'

    @staticmethod
    def assign_region(race, region, regionalities):
        if region in regionalities.columns:
            return regionalities.loc[race, region]
        else:
            return np.nan

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_results = ResultsDf(current_races=X['race']).load()

        # add region to each athlete
        df_results['region'] = None

        groups_indices = []
        for g, dgroup in df_results.groupby('country'):
            groups_indices.append((g, dgroup.index))

        for (country_code_iso3, indices) in groups_indices:
            df_results.loc[indices, 'region'] = self.get_region_from_ISO3(
                country_code_iso3, changeOceania=True)

        regionalities = (df_results
            .groupby(['race', 'region'])
            .size()
            .reset_index()
            .rename(columns={0: 'count'})
            .pivot(index='race', columns='region', values='count')

        )

        from_region = pd.DataFrame(list(
            regionalities.index.map(lambda race:
                {'index': race,
                'from_region': self.assign_region(
                    race, self.get_race_region(race, X), regionalities
                )}
            )
        ))

        from_region = from_region.set_index('index')

        from_region = pd.concat([
            regionalities.sum(axis=1).rename("total"),
            from_region], axis=1)

        from_region['perc_entrants_from_region'] = from_region['from_region'] / from_region['total']
        from_region['race'] = from_region.index

        return X.merge(from_region[['race', 'perc_entrants_from_region']],
                       left_on="race", right_on="race", how="left")


class FemaleRatio(BaseEstimator, TransformerMixin):
    """
    Compute the ratio females/males
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_results = ResultsDf(current_races=X['race']).load()

        df_results['gender'] = None
        df_results.loc[df_results.division.str.contains('M'), 'gender'] = 'M'
        df_results.loc[df_results.division.str.contains('F'), 'gender'] = 'F'

        gender_balance = {}
        for race in df_results.race.unique():
            gender_balance[race] = {}
            balance = pd.DataFrame(df_results.loc[df_results.race == race]
                 .groupby(['year', 'gender'])
                 .size()
                 .reset_index()
                 .rename(columns={0: 'count'})
                 .pivot(index='year', columns='gender', values='count')
            )
            balance['total'] = balance.F + balance.M
            balance['ratio_F'] = balance.F/balance.total
            gender_balance[race]['data'] = balance.to_dict(orient='records')
            gender_balance[race]['avg_F'] = balance.ratio_F.mean()

        gender_balance_df = pd.DataFrame([
            {'race': race,
             'perc_female': gender_balance[race]['avg_F'],
             'n_years': len(gender_balance[race]['data']),
             'avg_total': pd.DataFrame(gender_balance[race]['data']).mean()['total'],
             'type': '70.3' if '70.3' in race else 'full'
            } for race in gender_balance
        ])

        return X.merge(gender_balance_df[['race', 'perc_female']],
                       left_on="race", right_on="race", how="left")


class WorldChampionshipSlots(BaseEstimator, TransformerMixin):
    """
    Compute the ratio females/males
    """

    qualifyers = WorldChampionshipQualifyers().load()

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        wc_slots = pd.DataFrame(X['race'])
        wc_slots['wc_slots'] = 0

        for race, slots in self.qualifyers.loc[:, ["Competition", "Slots"]].values:
            racename = race.split("Ironman ")[1].lower()

            isHalf = False
            match = []
            if "70.3" in race:
                isHalf = True
                racename = racename.replace("70.3 ", "")
            racename = racename.replace("-", "").replace(" ", "")
            candidates = X.loc[X.race.str.contains(f"^{racename}", regex=True) == True, 'race'].values
            if isHalf:
                for c in candidates:
                    if "70.3" in c:
                        match.append(c)
            else:
                for c in candidates:
                    if "70.3" not in c:
                        match.append(c)

            if len(match) > 0:
                wc_slots.loc[wc_slots.race == match[0], 'wc_slots'] = slots

        return X.merge(wc_slots,
                       left_on="race", right_on="race", how="left")


class DistanceToNearestShoreline(BaseEstimator, TransformerMixin):
    """
    Compute distance to neareast coast
    """

    shorelines = Shorelines().load()

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """
        Calculate distance (in meters) between two lat/lon pairs
        """
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        lon1_rad = np.radians(lon1)
        lon2_rad = np.radians(lon2)
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad
        a = np.sqrt((np.sin(delta_lat / 2)) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * (np.sin(delta_lon / 2)) ** 2)
        d = 2 * 6371000 * np.arcsin(a)
        return d

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.assign(
            distance_to_nearest_shoreline=(
                X[['lat', 'lon']]
                    .transpose()
                    .apply(lambda race: np.min(
                        self.haversine(self.shorelines.lat,
                                       self.shorelines.lon,
                                       race['lat'],
                                       race['lon']
                                       ) / 1000  # in km
                            ))
            )
        )


class DistanceToNearestAirport(BaseEstimator, TransformerMixin):
    """
    Compute distance to neareast airport (+ international airport)
    """

    airports = Airports().load()

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """
        Calculate distance (in meters) between two lat/lon pairs
        """
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        lon1_rad = np.radians(lon1)
        lon2_rad = np.radians(lon2)
        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad
        a = np.sqrt((np.sin(delta_lat / 2)) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * (np.sin(delta_lon / 2)) ** 2)
        d = 2 * 6371000 * np.arcsin(a)
        return d

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        international_airports = self.airports.loc[
            self.airports.name.str.lower().str.contains("international")
        ]

        return pd.concat([
            X,
            X[['lat', 'lon']].transpose().apply(lambda race: pd.Series({
                'distance_to_nearest_airport': np.min(
                    self.haversine(self.airports.lat,
                                   self.airports.lon,
                                   race['lat'],
                                   race['lon']
                                   ) / 1000  # in km
                        ),
                'distance_to_nearest_airport_international': np.min(
                    self.haversine(international_airports.lat,
                                   international_airports.lon,
                                   race['lat'],
                                   race['lon']
                                   ) / 1000  # in km
                        )
                })).transpose()
        ], axis=1)


class GetNearbyFacilities(BaseEstimator, TransformerMixin):
    """
    Get information about nearby attractions, restaurants
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        metropolitanArea = MetropolitanArea().load()
        hotels = Hotels().load()
        restaurants = Restaurants().load()
        entertainment = Entertainment().load()
        nightLife = Nightlife().load()
        shops = Shops().load()
        bikeShops = BikeShops().load()
        pools = Pools().load()
        athleticCenters = AthleticCenters().load()
        fitnessCenters = FitnessCenters().load()

        return pd.concat([
            X,
            X.race.apply(lambda race: pd.Series({
                'n_metropolitan_cities': metropolitanArea[race]['totalCount'],
                'n_hotels': hotels[race]['poi_n_results'],
                'n_restaurants': restaurants[race]['poi_n_results'],
                'n_entertainment': entertainment[race]['poi_n_results'],
                'n_nightlife': nightLife[race]['poi_n_results'],
                'n_shops': shops[race]['poi_n_results'],
                'n_bike_shops': bikeShops[race]['poi_n_results'],
                'n_pools': pools[race]['poi_n_results'],
                'n_athletic_centers': athleticCenters[race]['poi_n_results'],
                'n_fitness_centers': fitnessCenters[race]['poi_n_results']
            }))
        ], axis=1)


class GetTypicalWeather(BaseEstimator, TransformerMixin):
    """
    Get information about typical weather
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        weather_icons_summary_df = Weather().getSummaryDataFrame()
        return X.merge(weather_icons_summary_df, left_on="race", right_on="race", how="left")


class GetTypicalTemperatures(BaseEstimator, TransformerMixin):
    """
    Get information about typical min/max temperatures
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        weather_temperatures_df = Weather().getTemperaturesDataFrame()
        return X.merge(weather_temperatures_df, left_on="race", right_on="race", how="left")


class RacingTimesStatistics(BaseEstimator, TransformerMixin):
    """
    Compute time statistics for races
    """
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_results = ResultsDf(current_races=X['race']).load()

        avg_times = (df_results.loc[((df_results[['swim', 'bike', 'run']] == -1).sum(axis=1) == 0) &
                                    ((df_results[['swim', 'bike', 'run']] < 0).sum(axis=1) == 0)]
             .groupby(["race", "year"])[['swim', 'bike', 'run']]
             .agg(['min', 'mean', 'max'])
             .reset_index()
             .groupby('race')
             .mean()[['swim', 'bike', 'run']]
        )
        avg_times.columns = ['_'.join(col).strip() for col in avg_times.columns.values]
        avg_times = avg_times.reset_index()

        return X.merge(avg_times, left_on="race", right_on="race", how="left")


class RunElevationMap(BaseEstimator, TransformerMixin):
    """
    Extract and resample elevation profile for the run
    """
    n_points = 200

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.assign(
            run_elevation_map=(
                X['race']
                    .map(lambda race:
                        json.dumps([{"x": x, "y": y} for x, y in zip(
                            # resample to 500 points
                            np.linspace(0, np.max(json.loads(X.loc[X['race'] == race, 'map'].values[0])['run']['distance']), self.n_points),
                          signal.resample(json.loads(X.loc[X['race'] == race, 'map'].values[0])['run']['elevation'], self.n_points)
                        )])

                    )
            )
        )


class BikeElevationMap(BaseEstimator, TransformerMixin):
    """
    Extract and resample elevation profile for the bike
    """
    n_points = 200

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.assign(
            bike_elevation_map=(
                X['race']
                    .map(lambda race:
                        json.dumps([{"x": x, "y": y} for x, y in zip(
                            # resample to 500 points
                            np.linspace(0, np.max(json.loads(X.loc[X['race'] == race, 'map'].values[0])['bike']['distance']), self.n_points),
                          signal.resample(json.loads(X.loc[X['race'] == race, 'map'].values[0])['bike']['elevation'], self.n_points)
                        )])

                    )
            )
        )


class IsHalf(BaseEstimator, TransformerMixin):
    """
    Is it a half ironman?
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return pd.concat([
            X,
            X.race.apply(lambda x: '70.3' in x).rename('is_70.3')
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
            'swim_type', 'ironkids_race', 'attractivity_score',
            'perc_entrants_from_country', 'perc_entrants_from_region',
            'perc_female', 'wc_slots', 'distance_to_nearest_shoreline',
            'distance_to_nearest_airport',
            'distance_to_nearest_airport_international', 'n_metropolitan_cities',
            'n_hotels', 'n_restaurants', 'n_entertainment', 'n_nightlife',
            'n_shops', 'n_bike_shops', 'n_pools', 'n_athletic_centers',
            'n_fitness_centers', 'weather_icon', 'weather_summary',
            'temperatureMin', 'temperatureMax', 'apparentTemperatureMin',
            'apparentTemperatureMax', 'swim_min', 'swim_mean', 'swim_max',
             'bike_min', 'bike_mean', 'bike_max', 'run_min', 'run_mean', 'run_max',
            'run_elevation_map', 'bike_elevation_map', 'is_70.3'
        ]
        return X.loc[:, columns_to_keep]
