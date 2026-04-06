import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.utils.class_weight import compute_class_weight


# -------------------------------------------------------------------
# 朴素贝叶斯加权版（解决类别不平衡）
# -------------------------------------------------------------------
class WeightedMultinomialNB(MultinomialNB):
    """在 fit 时对少数类自动加权"""

    def fit(self, X, y):
        classes = np.unique(y)
        weights = compute_class_weight("balanced", classes=classes, y=y)
        sample_weight = np.array([dict(zip(classes, weights))[label] for label in y])
        return super().fit(X, y, sample_weight=sample_weight)
