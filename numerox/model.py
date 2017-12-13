import json

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier as ETC
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA

try:
    from xgboost.sklearn import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

"""

Make your own model
-------------------

First take a look at the logistic and extratrees models below.

Your model MUST have a fit_predict method that takes two data objects as
input. The first is training data (dfit), the second is prediction data (dpre).

The fit_predict method MUST return two numpy arrays. The first contains the
ids, the second the predictions. Make sure that these two arrays stay aligned!

The models below inherit from The Model class. That is optional. But if you do
inherit from Model and if you place your parameters in self.p as is done in
the models below then you will get a nice printout (model name and parameters)
when you run your model.

None of the models below will be competitive in the Numerai tournament. You'll
have to make your own model. What numerox does is pass data to your model and
keep track of your predictions. If you already have a model then you can
make a thin wrapper around it, as is done below, to get it to run with numerox.

OK, now go make money!

"""


class Model(object):

    def hash(self, dfit, dpre):
        """"
        Hash of data, model name, and parameters dictionary if you have one.

        And if you are hashing it is a good idea to have a parameters
        dictionary.
        """
        h = []
        h.append(dfit.hash())
        h.append(dpre.hash())
        h.append(self.__class__.__name__)
        if hasattr(self, "p"):
            h.append(json.dumps(self.p, sort_keys=True))
        h = tuple(h)
        return hash(h)

    def __repr__(self):
        msg = ""
        model = self.__class__.__name__
        if hasattr(self, "p"):
            if len(self.p) == 0:
                msg += model + "()"
            else:
                msg += model + "("
                for name, value in self.p.items():
                    msg += name + "=" + str(value) + ", "
                msg = msg[:-2]
                msg += ")"
        else:
            msg += model + "()"
        return msg


class logistic(Model):

    def __init__(self, inverse_l2=0.0001):
        self.p = {'inverse_l2': inverse_l2}

    def fit_predict(self, dfit, dpre):
        model = LogisticRegression(C=self.p['inverse_l2'])
        model.fit(dfit.x, dfit.y)
        yhat = model.predict_proba(dpre.x)[:, 1]
        return dpre.ids, yhat


class extratrees(Model):

    def __init__(self, ntrees=100, depth=3, nfeatures=7, seed=0):
        self.p = {'ntrees': ntrees,
                  'depth': depth,
                  'nfeatures': nfeatures,
                  'seed': seed}

    def fit_predict(self, dfit, dpre):
        clf = ETC(criterion='gini',
                  max_features=self.p['nfeatures'],
                  max_depth=self.p['depth'],
                  n_estimators=self.p['ntrees'],
                  random_state=self.p['seed'],
                  n_jobs=-1)
        clf.fit(dfit.x, dfit.y)
        yhat = clf.predict_proba(dpre.x)[:, 1]
        return dpre.ids, yhat


class randomforest(Model):

    def __init__(self, ntrees=100, depth=3, max_features=2, seed=0):
        self.p = {'ntrees': ntrees,
                  'depth': depth,
                  'max_features': max_features,
                  'seed': seed}

    def fit_predict(self, dfit, dpre):
        clf = RFC(criterion='gini',
                  max_features=self.p['max_features'],
                  max_depth=self.p['depth'],
                  n_estimators=self.p['ntrees'],
                  random_state=self.p['seed'],
                  n_jobs=-1)
        clf.fit(dfit.x, dfit.y)
        yhat = clf.predict_proba(dpre.x)[:, 1]
        return dpre.ids, yhat


class xgboost(Model):

    def __init__(self, learning_rate=0.1, subsample=0.4, max_depth=5,
                 n_estimators=5, seed=0):
        self.p = {'learning_rate': learning_rate,
                  'subsample': subsample,
                  'max_depth': max_depth,
                  'n_estimators': n_estimators,
                  'seed': seed}
        if not HAS_XGBOOST:
            raise ImportError("You must install xgboost to use this model")

    def fit_predict(self, dfit, dpre):
        clf = XGBClassifier(learning_rate=self.p['learning_rate'],
                            subsample=self.p['subsample'],
                            max_depth=self.p['max_depth'],
                            n_estimators=self.p['n_estimators'],
                            seed=self.p['seed'],
                            nthread=-1)
        clf.fit(dfit.x, dfit.y)
        yhat = clf.predict_proba(dpre.x)[:, 1]
        return dpre.ids, yhat


# sklearn pipeline example
class logisticPCA(Model):

    def __init__(self, nfeatures=10, inverse_l2=1e-4):
        self.p = {'inverse_l2': inverse_l2,
                  'nfeatures': nfeatures}

    def fit_predict(self, dfit, dpre):
        pipe = Pipeline([('pca', PCA(n_components=self.p['nfeatures'])),
                         ("lr", LogisticRegression(C=self.p['inverse_l2']))])
        pipe.fit(dfit.x, dfit.y)
        yhat = pipe.predict_proba(dpre.x)[:, 1]
        return dpre.ids, yhat


# fast model for testing; always predicts 0.5
class fifty(Model):

    def __init__(self):
        self.p = {}

    def fit_predict(self, dfit, dpre):
        yhat = 0.5 * np.ones(len(dpre))
        return dpre.ids, yhat
