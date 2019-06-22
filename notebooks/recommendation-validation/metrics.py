import numpy as np
from sklearn.metrics import recall_score, precision_score, f1_score#, roc_curve, roc_auc_score

def binarize(arr, tol):
    """
    Convert continous valued array to binary. 
    """
    arr[arr < tol] = 0
    arr[arr >= tol] = 1
    return arr

# mean squared error
def mse(true, actual):
    return np.mean((true - actual) ** 2.)


# mean absolute error
def mae(true, actual):
    return np.mean(np.abs(true - actual))


def recall_at_k(true, pred, user_ids, k, tol=3.):
    unique_users = np.unique(user_ids)
    pred_binarized = binarize(pred.copy(), tol)
    recalls = np.zeros(unique_users.size)
    for i in range(unique_users.size):
        user_ind = user_ids == unique_users[i]
        user_true = true[user_ind]
        user_pred = pred[user_ind]
        user_pred_binarized = pred_binarized[user_ind]
        ranked_ind = np.argsort(-user_pred)[:k]
        recalls[i] = recall_score(user_true[ranked_ind], user_pred_binarized[ranked_ind])
    return np.mean(recalls[recalls > 0])


def precision_at_k(true, pred, user_ids, k, tol=3.):
    unique_users = np.unique(user_ids)
    pred_binarized = binarize(pred.copy(), tol)
    precisions = np.zeros(unique_users.size)
    for i in range(unique_users.size):
        user_ind = user_ids == unique_users[i]
        user_true = true[user_ind]
        user_pred = pred[user_ind]
        user_pred_binarized = pred_binarized[user_ind]
        ranked_ind = np.argsort(-user_pred)[:k]
        precisions[i] = precision_score(user_true[ranked_ind], user_pred_binarized[ranked_ind])
    return precisions

 
def MAP_at_k(true, pred, user_ids, k, tol=3.):
    unique_users = np.unique(user_ids)
    precisions_at_ks = np.zeros((k, unique_users.size))
    for i in range(k):
        precisions_at_ks[i] = precision_at_k(true, pred, user_ids, i+1, tol)
    return np.mean(precisions_at_ks[precisions_at_ks > 0])

def DCG_at_k(true, pred, user_ids, k):
    unique_users = np.unique(user_ids)
    dcgs = np.zeros(unique_users.size)
    for i in range(unique_users.size):
        user_ind = user_ids == unique_users[i]
        user_true = true[user_ind]
        user_pred = pred[user_ind]
        ranked_ind = np.argsort(-user_pred)[:k]
        user_relevances = user_true[ranked_ind]
        gains = 2. ** (user_relevances)
        discounts = np.log2(np.arange(user_relevances.size) + 2)
        dcgs[i] = np.sum(gains / discounts)
    return dcgs


def NDCG_at_k(true, pred, user_ids, k):
    actual_dcgs = DCG_at_k(true, pred, user_ids, k)
    best_dcgs = DCG_at_k(true, true, user_ids, k)
    return np.mean(actual_dcgs / best_dcgs)