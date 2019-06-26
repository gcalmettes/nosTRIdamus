import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


class BaseRecommender:
    def __init__(self, model, matrix=None, items_info=None, pos_to_item_mapping=None, df=None, name='Model'):
        self.name = name
        self.model = model
        if type(self.model) == type(None):
            # Default model is Nearest Neighbors
            self.model = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=5)
        self.matrix = matrix
        self.df = df
        if pos_to_item_mapping:
            self.items_info = items_info.loc[list(pos_to_item_mapping.values())]
        elif type(df) != type(None):
            self.items_info = items_info.loc[df.index]
        self.items_info_reset = self.items_info.reset_index()


class ALSRecommender(BaseRecommender):
    '''Alternative Least Square models from the implicit library'''
    def recommend(self, target, n=10, filterByField=False, valueToMatch=False, months_range=[0, 12], options={}):
        target_code = self.items_info.index.get_loc(target)
        similar = self.model.similar_items(target_code, len(self.items_info))
        
        df_distances = pd.DataFrame([
            [self.items_info_reset.loc[code, 'race'], distance]
                for (code,distance) in similar
        ], columns=['race', 'similarity'])
        
        df_order = df_distances.merge(self.items_info, left_on='race', right_on='race', how='left')
        if filterByField:
            df_order = df_order.loc[df_order[filterByField] == valueToMatch]

        # filter by months into months range
        df_order = df_order.loc[(df_order['month'] > months_range[0]) & (df_order['month'] <= months_range[1])]

        return df_order.iloc[:n+1]


class KNNRecommender(BaseRecommender):
    '''K-Nearest Neighbors from the scikit-learn library'''
    def recommend(self, target, n=10, filterByField=False, valueToMatch=False, months_range=[0, 12], options={}):
        
        # get weighted features and refit the model
        df = self.getTransformedMatrix(target, options)
        self.model.fit(df.values)

        # do predictions
        (distances, indices) = self.model.kneighbors(df.loc[target].values.reshape(1, -1), n_neighbors=len(self.items_info))
        df_distances = pd.concat([
            pd.Series(self.items_info_reset.loc[indices[0], 'race'].values, name='race'), 
            pd.Series(distances[0], name='similarity')
        ], axis=1)
        
        df_order = df_distances.merge(self.items_info, left_on='race', right_on='race', how='left')
        if filterByField:
            df_order = df_order.loc[df_order[filterByField] == valueToMatch]

        # filter by months into months range
        df_order = df_order.loc[(df_order['month'] > months_range[0]) & (df_order['month'] <= months_range[1])]

        return df_order.iloc[:n+1]

    def getTransformedMatrix(self, target, options):
        options['raceExperience'] = float(options['raceExperience'])
        options['raceSize'] = float(options['raceSize'])
        options['raceDifficulty'] = float(options['raceDifficulty'])

        to_transform = {}
        if options['raceExperience'] == 2:
           # looking for competition
           # put weights on world championship slots (4/5)
           # also on bike shops/poos/athletic centers, if they want to go train there
           to_transform['wc_slots'] = { 'dial_query': 5, 'dial': 5, 'increase': True }
           to_transform['n_bike_shops'] = { 'dial_query': 3, 'dial': 3, 'increase': True }
           to_transform['n_pools'] = { 'dial_query': 3, 'dial': 3, 'increase': True }
           to_transform['n_athletic_centers'] = { 'dial_query': 3, 'dial': 3, 'increase': True }
        if options['raceExperience'] == 0:
          # vacation (mostly distance to shoreline and number of restaurants)
          to_transform['distance_to_nearest_shoreline'] = { 'dial_query': 10, 'dial': 5, 'increase': False }
          to_transform['n_restaurants'] = { 'dial_query': 2, 'dial': 1.5, 'increase': True }
          to_transform['n_entertainment'] = { 'dial_query': 3, 'dial': 2, 'increase': True }

        to_transform['bike_score'] = { 'dial_query': options['raceDifficulty'], 'dial': options['raceDifficulty'], 'increase': True }
        to_transform['run_score'] = { 'dial_query': options['raceDifficulty'], 'dial': options['raceDifficulty'], 'increase': True }

        to_transform['entrants_count_avg'] = { 'dial_query': options['raceSize'], 'dial': options['raceSize'], 'increase': True }

        data_transformed = self.df.copy()

        for col in to_transform.keys():
            data_transformed[col] = transform_col(data_transformed, col, to_transform[col]['dial'], increase=to_transform[col]['increase'])
            data_transformed.loc[target, col] = transform_query(to_transform[col]['dial_query'])

        # return self.df
        return data_transformed


########################
# Weighting functions
########################

def sigmo_transform(x, base, amplitude, xhalf, slope):
    """
    Return the sigmoid curve for the x values.
    """
    return base + amplitude/(1.+np.exp(-slope*(x-xhalf)))


def transform_query(dial):
    return dial*sigmo_transform(dial, 0, 1, 3, 2.1)

    
def transform_col(df, column, dial, increase=True):
    factor = dial # slope of sigmoid
    if increase:
        return dial*sigmo_transform(df[column].values, 0, 1, 0.5, factor)[:, np.newaxis]
    else:
        return dial*(1-sigmo_transform(df[column].values, 0, 1, 0.5, factor))[:, np.newaxis]
