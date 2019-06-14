import numpy as np
import pandas as pd

from .get_model import pick_model, get_items

# Dictionary of possible models
models = {
  0: 'knn_sparse', # KNN on sparse matrix
  1: 'knn_svd_25',  # KNN on SVD factored matrix
  2: 'knn_svd_15'
}

items = get_items()

def get_recommendations(raceId, model_number=0, filterBy=False, valueToMatch=False):
    model,matrix = pick_model(models[int(model_number)])
    return get_most_similar_races_to(raceId, model=model, matrix=matrix, n=10, filterBy=filterBy, 
                              valueToMatch=valueToMatch, races_df=items, addTarget=True)
    

def get_filtered_races(filterBy, valueToMatch, df=items, returnIndices=False):
    if not filterBy:
        selection = df
    else:
        selection = df.loc[df[filterBy] == valueToMatch]
    if returnIndices:
        return selection.index.map(lambda x: df.index.get_loc(x)).tolist()
    else:
        return selection.index.values


def get_most_similar_races_to(raceId, model, matrix, n=10, filterBy=False, 
                              valueToMatch=False, races_df=items, addTarget=True):
    query_index = np.where(races_df.index == raceId)[0][0]
    total_n = races_df.shape[0]
    distances, indices = model.kneighbors(matrix[query_index].reshape(1, -1), n_neighbors = total_n)
    distances = distances.flatten()
    indices = indices.flatten()
    
    if filterBy:
        selection_idx = get_filtered_races(filterBy, valueToMatch, df=races_df, returnIndices=False)
        n = n if n<len(selection_idx) else len(selection_idx)
        out_distances = []
        out_races = []
        
        for indice,distance in zip(indices, distances):
            race = races_df.index[indice]
            if ((race in selection_idx) and (race != raceId)):
                out_races.append(race)
                out_distances.append(distance)
                if len(out_distances) >=n :
                    break
    else:
        out_races = races_df.index[indices[1:n+1]] #remove the race itself
        out_distances = list(distances[1:n+1]) #remove the race itself
    
    out_df = races_df.loc[out_races]
    if addTarget:
        out_df = pd.concat([pd.DataFrame(races_df.loc[raceId]).transpose(), out_df])
        out_distances.insert(0, 0)
    out_df['similarity'] = out_distances
        
    return out_df


def get_races_list():
    return items