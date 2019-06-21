import pickle
import scipy.sparse
import numpy as np
import pandas as pd
import json

from .recommenders import ALSRecommender, KNNRecommender

models_list = {
    # item-item collaborative filtering using Alternative Least Squares
    'ALS': {
        'name': 'ALS item-item CF',
        'model': './nostrappdamus/model/data/als_model.sav',
        'matrix': './nostrappdamus/model/data/als_sparse_matrix.npz',
        'load_matrix': scipy.sparse.load_npz,
        'hash_map': './nostrappdamus/model/data/als_hash.json',
        'class': ALSRecommender
    },
    'KNN_Content': {
        'name': 'KNN content-based',
        'model': './nostrappdamus/model/data/knn_content.sav',
        'matrix': './nostrappdamus/model/data/knn_content_matrix.npy',
        'hash_map': './nostrappdamus/model/data/knn_content_hash.json',
        'load_matrix': np.load,
        'class': KNNRecommender
    },
    'KNN_SVD_Content': {
        'name': 'KNN SVD 10 content-based',
        'model': './nostrappdamus/model/data/knn_svd_content.sav',
        'matrix': './nostrappdamus/model/data/knn_svd_content_matrix.npy',
        'hash_map': './nostrappdamus/model/data/knn_svd_content_hash.json',
        'load_matrix': np.load,
        'class': KNNRecommender
    }
}

look_up_items = {
    'file': './nostrappdamus/model/data/races_features.csv',
    'index_col': 'race'
}

# the first time it will be called, the variable will be assigned 
items = None
items_map = None

def get_model(model_name):
    config = models_list.get(model_name)
    if config:
        model_name = config['name']
        model_file = config['model']
        matrix_file = config['matrix'] 
        load = config['load_matrix']
        model_class = config['class']
        model_hash_map = config['hash_map']

    # load model
    with open(model_file, 'rb') as f:
        trained_model = pickle.load(f)
    # load matrix
    matrix = load(matrix_file)
    # make sure the items have been loaded into the variable space
    global items
    if type(items) == type(None):
        get_items()
    # load hash map
    with open(model_hash_map, 'r') as f:
        hash_map = json.loads(f.read())
    model = model_class(trained_model, matrix, items, hash_map, name=model_name)
    return model


def get_items():
    global items, items_map
    if type(items) != type(None):
        return items
    else:
        print('Loading items data for the first time!')
        # load races info
        items_full = pd.read_csv(look_up_items['file'], index_col=look_up_items['index_col'])
        columns_selection = [
            'racename', 'date', 'imlink', 'city', 'image_url', 'logo_url',
            'region', 'images', 'country_code', 'lat', 'lon', 'is_70.3'
        ]
        items = items_full.loc[:, columns_selection]
        # map info
        items_map = items_full.loc[:, [
            'run_elevation_map', 'bike_elevation_map', 'weather_icon', 'weather_summary',
            'bike_elevationGain', 'run_elevationGain'
        ]]
        items_map['run_elevation_map'] =  items_map['run_elevation_map'].map(lambda x: json.loads(x))
        items_map['bike_elevation_map'] =  items_map['bike_elevation_map'].map(lambda x: json.loads(x))
        return items


def get_items_map(raceId='boulder'):
    global items_map
    map_dict = items_map.loc[raceId].to_dict()
    map_dict['raceId'] = raceId
    return map_dict


