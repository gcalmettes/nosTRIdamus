import pickle
import scipy.sparse
import numpy as np
import pandas as pd

models = {
    'knn_sparse': {
        'model': './nostrappdamus/model/data/knn.sav',
        'matrix': './nostrappdamus/model/data/races_sparse_matrix.npz',
        'load_matrix': scipy.sparse.load_npz
    },
    'knn_svd_25': {
        'model': './nostrappdamus/model/data/knn_svd-25.sav',
        'matrix': './nostrappdamus/model/data/races_condensed_matrix_svd-25.npy',
        'load_matrix': np.load
    },
    'knn_svd_15': {
        'model': './nostrappdamus/model/data/knn_svd-15.sav',
        'matrix': './nostrappdamus/model/data/races_condensed_matrix_svd-15.npy',
        'load_matrix': np.load
    }
}

look_up_items = {
    'file': './nostrappdamus/model/data/races.csv',
    'index_col': 'race'
}

def pick_model(model_name):
    model = models.get(model_name)
    if model:
        file_model = model['model']
        file_matrix = model['matrix']

        # load model
        with open(file_model, 'rb') as f:
            trained_model = pickle.load(f)
        # load matrix
        matrix = model['load_matrix'](file_matrix)

        return (trained_model,matrix)
    else:
        return (False, False)


def get_items():
    # load races info
    items = pd.read_csv(look_up_items['file'], index_col=look_up_items['index_col'])
    columns_selection = [
        'racename', 'date', 'imlink', 'city', 'image_url', 'logo_url',
        'region', 'images', 'country_code', 'lat', 'lon', 'is_70.3'
    ]
    return items.loc[:, columns_selection]
