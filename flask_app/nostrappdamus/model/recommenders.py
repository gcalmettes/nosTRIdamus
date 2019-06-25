import pandas as pd


class BaseRecommender:
    def __init__(self, model, matrix, items_info, pos_to_item_mapping, name='Model'):
        self.name = name
        self.model = model
        self.matrix = matrix
        self.items_info = items_info.loc[list(pos_to_item_mapping.values())]
        self.items_info_reset = self.items_info.reset_index()


class ALSRecommender(BaseRecommender):
    '''Alternative Least Square models from the implicit library'''
    def recommend(self, target, n=10, filterByField=False, valueToMatch=False, months_range=[0, 12], options={}):
        target_code = self.items_info.index.get_loc(target)
        similar = self.model.similar_items(target_code, len(self.items_info))
        
        df_distances = pd.DataFrame([
            [self.items_info_reset.loc[code, 'race'], distance]
                for (code,distance) in similar
        ], columns=['race', 'distance'])
        
        df_order = df_distances.merge(self.items_info, left_on='race', right_on='race', how='left')
        if filterByField:
            df_order = df_order.loc[df_order[filterByField] == valueToMatch]

        # filter by months into months range
        df_order = df_order.loc[(df_order['month'] > months_range[0]) & (df_order['month'] <= months_range[1])]

        return df_order.iloc[:n+1]


class KNNRecommender(BaseRecommender):
    '''K-Nearest Neighbors from the scikit-learn library'''
    def recommend(self, target, n=10, filterByField=False, valueToMatch=False, months_range=[0, 12], options={}):
        target_code = self.items_info.index.get_loc(target)
        matrix = self.getTransformedMatrix(options)
        (distances, indices) = self.model.kneighbors(matrix[target_code].reshape(1, -1), n_neighbors=len(self.items_info))
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

    def getTransformedMatrix(self, options):
      
      return self.matrix