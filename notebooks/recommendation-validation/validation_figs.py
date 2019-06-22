import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.metrics import roc_curve

def uim_data(N=20, M=100, sparsity=0.1, frac_test=0.2, show=True, fill_num=0.9,
             fs=30):
    """
    Show splitting by frac_test using random holdout.
    """
    np.random.seed(1234)
    tot_size = N * M
    fill_size = int(np.round(tot_size * sparsity))
    uim = np.zeros(tot_size) + 0.1
    fill_ind = np.random.permutation(tot_size)[:fill_size]

    uim[fill_ind] = fill_num

    uim = uim.reshape(N, M)
    fig = plt.figure(figsize=(20, 4))
    cmap = sns.cubehelix_palette(3, as_cmap=True)
    sns.heatmap(uim, cbar=False, xticklabels=False,
                                 yticklabels=False)
    plt.xlabel('Items', fontsize=fs)
    plt.ylabel('Users', fontsize=fs)
    if show:
        plt.show()
        plt.close()
    return uim, fill_num

def leave_k_out(uim, fill_num, frac_test=0.2, test_num=0.5, fs=30, show=True):
    """
    Show splitting by frac_test using random holdout.
    """
    N_user, M_item = uim.shape
    uim = uim.ravel()
    entries = np.where(uim == fill_num)[0]

    N = entries.size
    N_test = int(np.round(frac_test * N))
    test_ind = np.random.permutation(N)[:N_test]
    uim[entries[test_ind]] = test_num

    fig = plt.figure(figsize=(20, 4))
    cmap = sns.cubehelix_palette(3, as_cmap=True)
    sns.heatmap(uim.reshape(N_user, M_item), cbar=False, xticklabels=False,
                                 yticklabels=False)
    plt.xlabel('Items', fontsize=fs)
    plt.ylabel('Users', fontsize=fs)
    if show:
        plt.show()
        plt.close()

def M_fold(uim, fill_num, frac=0.5, test_num=0.5, fs=30, show=True):
    """
    Show splitting by frac_test using random holdout.
    """
    N_user, M_item = uim.shape
    uim = uim.ravel()
    entries = np.where(uim == fill_num)[0]

    N = entries.size
    N_holdout = np.int(np.round(frac * N))
    N_test = np.int(np.round(frac * N_holdout))
    holdout_ind = entries[N_holdout:]
    test_ind = holdout_ind[np.random.permutation(N_holdout)[:N_test]]
    uim[test_ind] = test_num

    fig = plt.figure(figsize=(20, 4))
    cmap = sns.cubehelix_palette(3, as_cmap=True)
    sns.heatmap(uim.reshape(N_user, M_item), cbar=False, xticklabels=False,
                                 yticklabels=False)
    plt.xlabel('Items', fontsize=fs)
    plt.ylabel('Users', fontsize=fs)
    if show:
        plt.show()
        plt.close()

def user_item_hists(urm, fs=6, bins=50, a=0.4, log=False, font=25):
    """
    Plot the distribution of the number of ratings, accross users and items.
    """
    nonzero_urm = urm > 0
    user_counts = np.sum(urm, axis=1)
    item_counts = np.sum(urm, axis=0)

    if log:
        ylabel = 'Log(Frequency)'
    else:
        ylabel = 'Frequency'

    plt.figure(figsize=(2 * fs, fs))
    plt.subplot(121)
    plt.hist(user_counts, bins=bins, alpha=a, density=True, log=log,
            label='User counts')
    plt.xlabel('Number of ratings', fontsize=font)
    plt.ylabel(ylabel, fontsize=font)
    plt.legend(fontsize=font)
    plt.subplot(122)
    plt.hist(item_counts, bins=bins, alpha=a, density=True, log=log,
            label='Item counts')
    plt.xlabel('Number of ratings', fontsize=font)
    plt.ylabel(ylabel, fontsize=font)
    plt.legend(fontsize=font)

    return user_counts, item_counts

def get_se_dists(test, pred):
    """
    Compute the global and conditional squared errors.
    """
    se = (test - pred) ** 2.
    ind = test > 0
    se_glob = se[ind]

    se_user = np.zeros(se.shape[0])
    for i in range(se.shape[0]):
        se_user[i] = np.mean(se[i][ind[i]])
    se_user[np.isnan(se_user)] = np.mean(se_glob)

    se_item = np.zeros(se.shape[1])
    for i in range(se.shape[1]):
        se_item[i] = np.mean(se[:, i][ind[:, i]])
    se_item[np.isnan(se_item)] = np.mean(se_glob)
    return se_glob, se_user, se_item

def se_hists(test, pred, fs=6, bins=50, a=0.5, log=False, font=25, max_err=5):
    """
    Plot the squared error distributions - globally, by user, by item.
    """
    se_glob, se_user, se_item = get_se_dists(test, pred)

    if log:
        ylabel = 'Log(Relative Frequency)'
    else:
        ylabel = 'Relative Frequency'

    plt.figure(figsize=(fs, fs))
    plt.hist(se_glob, bins=bins, alpha=a*2, density=True, log=log,
            label='Sq. Error')
    plt.hist(se_user, bins=bins, alpha=a, density=True, log=log,
            label='Sq. Error by user')
    plt.hist(se_item, bins=bins, alpha=a, density=True, log=log,
            label='Sq. Error by item')
    plt.xlabel('Squared Error', fontsize=font)
    plt.ylabel(ylabel, fontsize=font)
    plt.xlim(0, max_err)
    plt.legend(fontsize=font/2)

def se_hists_percentile(test, pred, user_counts, item_counts, percentile=10, fs=6, bins=20, a=0.5, log=False, font=25, max_err=10):
    """
    Plot the squared error distributions - globally, by user, by item.
    """
    se_glob, se_user, se_item = get_se_dists(test, pred)
    user_ind = np.argsort(user_counts)
    item_ind = np.argsort(item_counts)
    Nuser = np.int(np.round(0.01 * percentile * user_ind.size))
    Nitem = np.int(np.round(0.01 * percentile * item_ind.size))

    if log:
        ylabel = 'Log(Relative Frequency)'
    else:
        ylabel = 'Relative Frequency'

    plt.figure(figsize=(2 * fs, fs))
    plt.subplot(121)
    plt.hist(se_user[user_ind[-Nuser:]], bins=bins, alpha=a/2, density=True, log=log,
            label='Sq. Error by user', color='g')
    plt.hist(se_item[item_ind[-Nitem:]], bins=bins, alpha=a/2, density=True, log=log,
            label='Sq. Error by item', color='r')
    plt.xlabel('Squared Error', fontsize=font)
    plt.ylabel(ylabel, fontsize=font)
    plt.xlim(0, max_err)
    plt.title('Top %d%%' % percentile, fontsize=font)
    plt.legend(fontsize=font/2)

    plt.subplot(122)
    plt.hist(se_user[user_ind[:Nuser]], bins=bins, alpha=a/2, density=True, log=log,
            label='Sq. Error by user', color='g')
    plt.hist(se_item[item_ind[:Nitem]], bins=bins, alpha=a/2, density=True, log=log,
            label='Sq. Error by item', color='r')
    plt.xlabel('Squared Error', fontsize=font)
    plt.ylabel(ylabel, fontsize=font)
    plt.xlim(0, max_err)
    plt.title('Bottom %d%%' % percentile, fontsize=font)
    plt.legend(fontsize=font/2)

def get_ind_user(nonzero_ind, user_ind):
    """
    Construct indices for users with entries in a given index list.
    """
    users = np.array([], dtype=np.int)
    items = np.array([], dtype=np.int)
    for i in range(nonzero_ind[0].size):
        if nonzero_ind[0][i] in user_ind:
            users = np.append(users, nonzero_ind[0][i])
            items = np.append(items, nonzero_ind[1][i])
    return (users, items)

def get_ind_item(nonzero_ind, item_ind):
    """
    Construct indices for items with entries in a given index list.
    """
    users = np.array([], dtype=np.int)
    items = np.array([], dtype=np.int)
    for i in range(nonzero_ind[1].size):
        if nonzero_ind[1][i] in item_ind:
            users = np.append(users, nonzero_ind[0][i])
            items = np.append(items, nonzero_ind[1][i])
    return (users, items)

def user_item_rocs(y_true, y_pred, user_counts, item_counts, nonzero_ind,
                   percentile=10, fs=6, font=25, a=0.5):
    """
    Plot ROC curves, including those conditioned on users, items at Bottom
    percentile of ratings distribution.
    """
    user_ind = np.argsort(user_counts)
    item_ind = np.argsort(item_counts)
    Nuser = np.int(np.round(0.01 * percentile * user_ind.size))
    Nitem = np.int(np.round(0.01 * percentile * item_ind.size))


    plt.figure(figsize=(8, 8))
    fpr, tpr, thresholds = roc_curve(y_true[nonzero_ind], y_pred[nonzero_ind])
    plt.plot(fpr, tpr, lw=2, label='All')

    # users
    ind = get_ind_user(nonzero_ind, user_ind[:Nuser])
    yt, yp = y_true[ind], y_pred[ind]
    fpr, tpr, thresholds = roc_curve(yt, yp)
    plt.plot(fpr, tpr, lw=2, color='g', alpha=a, label='Bottom 10% Users')

    # items
    ind = get_ind_item(nonzero_ind, item_ind[:Nitem])
    yt, yp = y_true[ind], y_pred[ind]
    fpr, tpr, thresholds = roc_curve(yt, yp)
    plt.plot(fpr, tpr, lw=2, color='r', alpha=a, label='Bottom 10% Items')

    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('FPR', fontsize=font)
    plt.ylabel('TPR', fontsize=font)
    plt.legend(loc=2, fontsize=font/2)

def k_DCG(true, pred, user_ids, k):
    """
    Return k DCGs per user.
    """
    unique_users = np.unique(user_ids)
    dcgs = np.ones((unique_users.size, k))
    for i in range(unique_users.size):
        user_ind = user_ids == unique_users[i]
        user_true = true[user_ind]
        user_pred = pred[user_ind]
        ranked_ind = np.argsort(-user_pred)[:k]
        user_relevances = user_true[ranked_ind]
        gains = 2. ** (user_relevances)
        discounts = np.log2(np.arange(user_relevances.size) + 2)
        dcgs[i, :gains.size] = gains / discounts
    return dcgs

def k_NDCG(true, pred, user_ids, k):
    """
    Not actually NDCG.  Return predicted and best DCGs for comparison.
    """
    actual_dcgs = k_DCG(true, pred, user_ids, k)
    best_dcgs = k_DCG(true, true, user_ids, k)
    actual_dcgs /= np.max(actual_dcgs, axis=1)[:, None]
    best_dcgs /= np.max(best_dcgs, axis=1)[:, None]
    return actual_dcgs, best_dcgs

def ndcg_plot(y_true, y_pred, user_ids, k, N, font=40, fs=6, seed=1234):
    """
    Plot predicted and best DCGs.  Two columns of random users, one for the
    users with the best MSE.
    """
    np.random.seed(seed)
    se = (y_true - y_pred) ** 2.
    unique_users = np.unique(user_ids)
    user_mses = np.zeros(unique_users.size)
    for i in range(unique_users.size):
        user_mses[i] = np.std(se[user_ids == unique_users[i]])

    rand_user_ids = unique_users[np.random.permutation(unique_users.size)[:N]]
    ind = np.array([], np.int)
    for i in range(N):
        ind = np.append(ind, np.where(user_ids == rand_user_ids[i])[0])
    a, b = k_NDCG(y_true[ind], y_pred[ind], user_ids[ind], k)

    cmap = sns.cubehelix_palette(as_cmap=True, reverse=True)
    plt.figure(figsize=(3 * fs, 2 * fs))
    ax = plt.subplot(231)
    plt.imshow(a, interpolation='nearest', cmap=cmap)
    ax.text(0.5, 1.05, 'Random %d Users' % N, horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font)
    ax.text(-0.05, 0.5, 'Users', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font/2,
            rotation=90)
    ax.text(-0.15, 0.5, 'Predicted DCGs', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font,
            rotation=90)
    plt.axis('off')
    ax = plt.subplot(234)
    plt.imshow(b, interpolation='nearest', cmap=cmap)
    plt.axis('off')
    ax.text(0.5, -0.05, 'Recommended Items', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font/2)
    ax.text(-0.05, 0.5, 'Users', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font/2,
            rotation=90)
    ax.text(-0.15, 0.5, 'Best Possible DCGs', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font,
            rotation=90)

    rand_user_ids = unique_users[np.random.permutation(unique_users.size)[:N]]
    ind = np.array([], np.int)
    for i in range(N):
        ind = np.append(ind, np.where(user_ids == rand_user_ids[i])[0])
    a, b = k_NDCG(y_true[ind], y_pred[ind], user_ids[ind], k)

    cmap = sns.cubehelix_palette(as_cmap=True, reverse=True)
    ax = plt.subplot(232)
    plt.imshow(a, interpolation='nearest', cmap=cmap)
    plt.axis('off')
    ax.text(0.5, 1.05, 'Random %d Users' % N, horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font)
    ax = plt.subplot(235)
    plt.imshow(b, interpolation='nearest', cmap=cmap)
    plt.axis('off')
    ax.text(0.5, -0.05, 'Recommended Items', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font/2)

    best_user_ids = unique_users[np.argsort(user_mses)[:N]]
    ind = np.array([], np.int)
    for i in range(N):
        ind = np.append(ind, np.where(user_ids == best_user_ids[i])[0])
    a, b = k_NDCG(y_true[ind], y_pred[ind], user_ids[ind], k)
    ax = plt.subplot(233)
    plt.imshow(a, interpolation='nearest', cmap=cmap)
    ax.text(0.5, 1.05, 'Best %d Users' % N, horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font)
    plt.axis('off')
    ax = plt.subplot(236)
    plt.imshow(b, interpolation='nearest', cmap=cmap)
    plt.axis('off')
    ax.text(0.5, -0.05, 'Recommended Items', horizontalalignment='center',
            verticalalignment='center', transform=ax.transAxes, fontsize=font/2)

    plt.tight_layout(w_pad=0.1)

if __name__ == '__main__':
    uim, fill_num = uim_data(show=False)
    leave_k_out(uim.copy(), fill_num)
    M_fold(uim.copy(), fill_num)
