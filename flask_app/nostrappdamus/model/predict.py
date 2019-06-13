import pickle
import scipy.sparse
import numpy as np
import pandas as pd


# load sparce matrix
sparse_matrix = scipy.sparse.load_npz('./nostrappdamus/model/data/races_sparse_matrix.npz')
# load races info
races = pd.read_csv("./nostrappdamus/model/data/races.csv", index_col='race')

# load the model from disk
with open('./nostrappdamus/model/data/knn.sav', 'rb') as f:
    knn_model = pickle.load(f)

def test():
    return 1

def get_filtered_races(filterBy, valueToMatch, df=races, returnIndices=False):
    if not filterBy:
        selection = df
    else:
        selection = df.loc[df[filterBy] == valueToMatch]
    if returnIndices:
        return selection.index.map(lambda x: df.index.get_loc(x)).tolist()
    else:
        return selection.index.values

def get_most_similar_races_to(raceId, model=knn_model, n=10, filterBy=False, 
                              valueToMatch=False, races_df=races, addTarget=True):
    query_index = np.where(races_df.index == raceId)[0][0]
    total_n = races_df.shape[0]
    distances, indices = model.kneighbors(sparse_matrix[query_index].reshape(1, -1), n_neighbors = total_n)
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
    return races