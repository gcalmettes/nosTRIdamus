import os
import gzip
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix

def fetch_gowalla_checkin_data(directory_path='./', min_counts=20,
                               set_to_one=True, save_ulm=True,
                               ulm_filename='gowalla_ulm.npz'):
    """
    This routine fetches the Gowalla check-in data and returns a sparse scipy
    matrix, which is users by locations. First we check to see if the data is on
    disk, then format and remove locations with low numbers of check-ins, if
    desired set entries to one, and finally return.

    Args:
        min_counts [Optional(int)]: Threshold for minimum number of check-ins.
        set_to_one [Optional(boolean)]: Flag to set ulm entries to one.
    Return:
        ulm [scipy sparce matrix (float)]: User-location matrix.
    """
    # check for the ulm on disk, return it if True
    if os.path.isfile(directory_path + ulm_filename):
        return load_sparse(directory_path + ulm_filename)

    # check to see if original data is on disk, if not get it
    filename = 'loc-gowalla_totalCheckins.txt.gz'
    filename = 'gwl_checkins.tsv.gz'
    if not os.path.isfile(directory_path + filename):
        try:
            import wget
        except ImportError:
            m = 'wget required.  Consider downloading first if '
            m += 'you dont want to install via pip'
            raise ImportError()
        url = 'https://snap.stanford.edu/data/%s' % filename
        wget.download(url, directory_path + filename)

    # Load into pandas dataframe to ease some manipulation.
    with gzip.open(directory_path + filename, 'rb') as f:
        df = pd.pandas.read_table(f, delimiter='\t', header=None,
                                  names=['user', 'location', 'rating'])

    # filter out locations below min_counts
    counts_groupbyid = df[['location', 'rating']].groupby('location',
                                                         as_index=False)
    counts = counts_groupbyid.size()
    df = df[df['location'].isin(counts.index[counts >= min_counts])]

    # unroll to numpy and get uniques
    location_ids = df['location'].values
    user_ids = df['user'].values
    uniq_locations = np.sort(np.unique(location_ids))
    uniq_users = np.sort(np.unique(user_ids))

    # create dict to map ids to row, col
    user_map = {}
    for i in range(uniq_users.size):
        user_map[uniq_users[i]] = i
    location_map = {}
    for i in range(uniq_locations.size):
        location_map[uniq_locations[i]] = i

    # go through and create row, col assignments
    N = location_ids.size
    user_inds = np.zeros(N)
    location_inds = np.zeros(N)
    for i in range(N):
        user_inds[i] = user_map[user_ids[i]]
        location_inds[i] = location_map[location_ids[i]]

    # create the matrix
    ulm = csr_matrix((np.ones(N), (user_inds, location_inds)),
                      shape=(uniq_users.size, uniq_locations.size),
                      dtype=np.float)
    if set_to_one:
        ulm = ulm.minimum(1)

    if save_ulm:
        save_sparse(directory_path + ulm_filename, ulm)

    return ulm

def fetch_movielens_data(directory_path='./ml-100k/'):
    """
    Create the user-ratings matrix from MovieLens 100k data.  This assumes the
    data has already been downloaded.  These functions have been lifted from
    Ethan's blog - http://bit.ly/1YvzkE2

    Args:
        directory_path [Optional(string)]: path to directory where u.data lives.
    Returns:
        ratings [numpy.ndarray]: numpy user-ratings array.
    """
    names = ['user_id', 'item_id', 'rating', 'timestamp']
    df = pd.read_csv(directory_path + 'u.data', sep='\t', names=names)
    n_users = df.user_id.unique().shape[0]
    n_items = df.item_id.unique().shape[0]
    ratings = np.zeros((n_users, n_items))
    for row in df.itertuples():
        ratings[row[1]-1, row[2]-1] = row[3]
    return ratings

def train_test_split(ratings, frac_test=0.2, impute=True, seed=1234):
    """
    Split the MovieLens data into train/test, mostly follows version found here,
    http://bit.ly/1YvzkE2, but also allows imputation of zeros in training data
    with mean values of item ratings.

    Args:
        ratings [numpy.ndarray]: user-ratings matrix
        frac_test [Optional(float)]: Fractional amount of entries to test.
        impute [Optional(boolean)]: Flag to impute zeros with means of items.
        seed [Optional(int)]: Integer to fix random number generator.

    Returns:
        train [numpy.ndarray]: training user-ratings matrix
        test [numpy.ndarray]: test user-ratings matrix
    """
    # init
    np.random.seed(seed)
    test = np.zeros(ratings.shape)
    train = ratings.copy()

    # get non-zero entry indices, construct test indices
    nonzero_ind = np.where(train > 0)
    N = nonzero_ind[0].size
    N_test = np.int(np.round(frac_test * N))
    ind = np.random.permutation(N)[:N_test]
    test_users = nonzero_ind[0][ind]
    test_items = nonzero_ind[1][ind]

    # assign
    test[test_users, test_items] = train[test_users, test_items].copy()
    train[test_users, test_items] = 0.

    if impute:
        pos_ind = train > 0
        # set means to mean of all non-zero entries (for unrated items)
        means = np.zeros(train.shape[1]) + np.mean(train[pos_ind])

        # for each item, revise mean to mean of item
        for i in range(means.size):
            item = train[:, i]
            ind = item > 0.
            if any(ind):
                means[i] = np.mean(item[ind])

        mean_train = np.tile(means, (train.shape[0], 1))
        mean_train[pos_ind] = train[pos_ind].copy()
        train = mean_train

        # re-zero test data in train
        train[test_users, test_items] = 0.

    # Test and training are truly disjoint
    assert(np.all((train * test) == 0))

    return train, test

def save_sparse(filepath, arr):
    """
    Save a scipy csr sparse matrix to numpy npz file.
    """
    np.savez(filepath, data=arr.data, indices=arr.indices, indptr=arr.indptr,
             shape=arr.shape)

def load_sparse(filepath):
    """
    Load a scipy csr sparse matrix from numpy npz file.
    """
    loader = np.load(filepath)
    return csr_matrix((loader['data'], loader['indices'], loader['indptr']),
                    shape=loader['shape'])
