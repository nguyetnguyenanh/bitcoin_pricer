# %load GenericModel.py
import os
from datetime import datetime, timedelta
# from sklearn.externals\
import joblib
import pandas as pd
import matplotlib.pyplot as plt


from GoogleTrendAPI import GoogleTrendAPI
from FinanceAPI import FinanceAPI

class GenericModel:
    """Abstract class
    Class variables MODEL_NAME, MODEL_CLASS, EXTRA_MODEL_ARGS are to be overwritten by child class
    Class methods:
    __init__: initiate Finance_api, GoogleTrendApi, and model
    train: train the model given by MODEL_CLASS or saved in MODEL_NAME
    predict: predict bitcoin price
    score: calculate R^2 score, using data from recent dates as test data
    save: save model to MODEL_NAME
    """
    MODEL_NAME = ''  # file path of saved model. to be be overwritten by child class
    MODEL_CLASS = None  # to be overwritten by child class
    EXTRA_MODEL_ARGS = {}  # to be overwritten by child class

    def __init__(self, finance_api=None, google_trend_api=None):
        """Constructor:
        - Initiate finance_api and google_trend_api
        - load previously saved model, or create a new instance
        """
        self.finance_api = finance_api if finance_api is not None else FinanceAPI()  # initiate finance api if not
        # provided (default)
        self.google_trend_api = google_trend_api if google_trend_api is not None else GoogleTrendAPI()
        # initiate Google api if not provided (default)

        if os.path.isfile(self.MODEL_NAME):  # Return True if 'MODEL_NAME' is an existing regular file
            self.model = joblib.load(self.MODEL_NAME)  # load the model from file
            print(self.MODEL_NAME, 'model file exists and loaded')  # scaffolding code
        else:  # call an instance of model class (from scikit-learn)
            self.model = self.MODEL_CLASS(**self.EXTRA_MODEL_ARGS)  #

    def gather_data(self, start, end):
        """Gather the data from the Google and Yahoo APIs
        return tuple X_train,y_train,X_test,y_test) where train data is the first 2/3 of the data
        """
        google_trend_df = self.google_trend_api.get_data(start, end)
        # shape (days,2), columns  = Date , bitcoin
        finance_df = self.finance_api.get_data(start, end)
        # shape (days,5), columns  = Date , ^GSPC , ^VIX, Volume , BTC-USD
        df = finance_df.merge(google_trend_df, on=['Date'])
        df = df.dropna()
        df_train = df[:int(df.shape[0] * 2 / 3)]
        X_train = df_train[['^GSPC', '^VIX', 'Volume', 'bitcoin']]  # input
        y_train = df_train['BTC-USD']  #

        df_test = df[int(df.shape[0] * 2 / 3):]
        X_test = df_train[['^GSPC', '^VIX', 'Volume', 'bitcoin']]  # input
        y_test = df_train['BTC-USD']  #

        return (X_train, y_train, X_test, y_test)

    def train(self, start, end):
        """ Train the model with data
        INPUT: model object, start date, end date
        OUTPUT: return None, fit the model to data
        """
        X, y, _, _ = self.gather_data(start, end)
        self.model.fit(X, y)  # fit the data to the model

    def plot_data(self, start, end):
        """Plot the train data"""
        X, y, _, _ = self.gather_data(start, end)  # get the train data
        # plotting
        f = plt.figure(figsize=(10, 10))
        ax = f.add_subplot(2, 2, 1)
        ax.plot(X.index, X[['^GSPC']], 'o-')
        ax.set_xlabel('days since ' + str(start.year) + '-' + str(start.month) + '-' + str(start.day))
        ax.set_ylabel('GSPC')
        ax = f.add_subplot(2, 2, 2)
        ax.plot(X.index, X[['^VIX']], 'o-')
        ax.set_xlabel('days since ' + str(start.year) + '-' + str(start.month) + '-' + str(start.day))
        ax.set_ylabel('VIX')
        ax = f.add_subplot(2, 2, 3)
        ax.plot(X.index, X[['Volume']], 'o-')
        ax.set_xlabel('days since ' + str(start.year) + '-' + str(start.month) + '-' + str(start.day))
        ax.set_ylabel('Volume')
        ax = f.add_subplot(2, 2, 4)
        ax.plot(X.index, X[['bitcoin']], 'o-')
        ax.set_xlabel('days since ' + str(start.year) + '-' + str(start.month) + '-' + str(start.day))
        ax.set_ylabel('Google Trend for \'bitcoin\' ')

        f2 = plt.figure(figsize=(5, 5))
        plt.plot(y.index, y, 'o-')

    def predict(self, attributes):
        """Predict using the linear model
        INPUT: finance data '^GSPC', '^VIX', 'Volume' and Google Trend data for 'bitcoin'
        OUTPUT: bitcoin price
        """
        df = pd.DataFrame([attributes], columns=['^GSPC', '^VIX', 'Volume', 'bitcoin'])
        return self.model.predict(df)

    def score(self, start, end):
        """Return the coefficient of determination R^2 of the prediction
        using data from recent dates as test data
        R = 1 means prediction = data (ideal case), R = 0 means prediction always = mean(true)"""

        _, _, X, y = self.gather_data(start, end)  # get the test data
        return self.model.score(X, y)

    def save(self):  # save model object to file, path given by MODEL_NAME
        joblib.dump(self.model, self.MODEL_NAME)
