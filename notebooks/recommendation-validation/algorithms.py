import numpy as np


class CosSimilarityRecommender(object):
    """
    Cosine similarity recommender.
    """
    def __init__(self, kind='item'):
        assert kind in ['user', 'item'], 'kind must be user or item'
        self.kind = kind

    def fit(self, uim):
        self.similarity = self.cos_similarity(uim)

    def cos_similarity(self, uim, epsilon=1e-9):
        # epsilon -> small number for handling dived-by-zero errors
        if self.kind == 'user':
            sim = uim.dot(uim.T)
        else:
            sim = uim.T.dot(uim)
        norms = np.array([np.sqrt(np.diagonal(sim))]) + epsilon
        return np.maximum(epsilon, sim / norms / norms.T)

    def predict(self, uim):
        if self.kind == 'user':
            sdotr = self.similarity.dot(uim)
            predicts = sdotr / np.array([np.abs(self.similarity).sum(axis=1)]).T
        else:
            rdots = uim.dot(self.similarity)
            predicts = rdots / np.array([np.abs(self.similarity).sum(axis=1)])
        return predicts

class SVDRecommender(object):
    """
    SVD Recommender.  This is just simple PCA, and is not regularized like
    'SVD++'.
    """
    def __init__(self, k=None, remove_bias='user', epsilon=1.e-9):
        self.k = k
        self.epsilon = epsilon
        self.remove_bias

    def fit(self, uim):
        if remove_bias == 'user':
            biases = np.mean(train, axis=1)[:, None]
        elif remove_bias == 'item':
            biases = np.mean(train, axis=1)[:, None]
        else:
            biases = np.zeros_like(uim)
        U, s, VT = np.linalg.svd(uim - biases, full_matrices=False)

        # dimensionality reduction
        Uk = U[:, :k]
        Sk = np.sqrt(np.diag(s)[:k, :k])
        VTk = V[:k, :]

        UkSk = np.dot(Uk, Sk)
        SkVTk = np.dot(Sk, VTk)
        self.reconstructed = np.maximum(self.epsilon, np.dot(UkSk, SkVTk) +
                                        biases)
    def predict(self):
        return self.reconstructed
