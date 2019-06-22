import os
import gzip
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix


def fetch_gowalla_checkin_data(directory_path='./', min_counts=20,
                               set_to_one=True):
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
    # check to see if data is on disk, if not get it
    filename = 'loc-gowalla_totalCheckins.txt.gz'
    if not os.path.isfile(directory_path + filename):
        try:
            import wget
        except ImportError:
            raise ImportError('wget required.  Consider downloading first if
                               you dont want to install via pip')
        url = 'https://snap.stanford.edu/data/%s' % filename
        wget.download(url, filepath)

    # Load into pandas dataframe to ease some manipulation.
    with gzip.open(filepath, 'rb') as f:
        df = pd.pandas.read_table(f, delimiter='\t', header=None,
                                  names=['user', 'location', 'rating'])

    # filter out locations below min_counts
    count_groupbyid = df[['location', 'rating']].groupby('location',
                                                         as_index=False)
    count = count_groupbyid.size()
    df = df[df['location'].isin(loc_count.index[loc_count >= min_counts])]

    # unroll to numpy and get uniques
    location_ids = df['location'].values
    user_ids = df['user'].values
    uniq_locations = np.sort(np.unique(loc_ids))
    uniq_users = np.sort(np.unique(user_ids))

    # create dict to map ids to row, col
    user_map = {}
    for i in range(uniq_users.size):
        usr_map[uniq_users[i]] = i
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

    return ulm
