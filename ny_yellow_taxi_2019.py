import pandas as pd
import dask.dataframe as dd
from dask.diagnostics import ProgressBar
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV
from scipy import stats
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
pd.options.display.width = 0
pd.options.display.max_rows = None
pd.options.display.float_format = "{:.2f}".format

'''Reading data from CSV'''
print("--- Reading data ---\n")
data = pd.read_csv('yellow_tripdata_2019-01.csv')

data = data[['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance', 'RatecodeID', 'PULocationID', 'DOLocationID',
             'payment_type', 'fare_amount']]

# print(data.head())
# print(data.describe())

'''CHECK FOR NaNs (generally and in detail)'''
# pd.set_option('use_inf_as_na', True)
# data = data.replace([np.inf, -np.inf], 0).dropna(subset=data.columns, how="all")
#
# missing_values_all = data.isnull().sum().sum()
# print("\nHow many NaNs in dataset?\n", missing_values_all)
#
# missing_values = data.isnull().sum()
# missing_count = (missing_values / data.index.size * 100)
# print("\nWhere are the NaNs:\n", missing_count)

'''Throwing out unknown zones 264 & 265 and zone 1 (Newark Airport)'''
print("--- Throwing out bad data points ---\n")
data = data[data['PULocationID'] != 1]
data = data[data['DOLocationID'] != 1]
data = data[data['PULocationID'] < 264]
data = data[data['DOLocationID'] < 264]
data = data[data['RatecodeID'] == 1]
data = data[data['fare_amount'] > 0]
data['trip_distance'] = (data['trip_distance'] * 1.609344).round(decimals=2) # getting KM
data = data[data['trip_distance'] >= 0.5]
data = data[data['trip_distance'] < 100]
data = data[data['fare_amount'] < 150]
data = (data[data['fare_amount'] >= 2.5])
data = data[data['payment_type'] <= 2]

# print(data.describe())

'''Converting to datetime'''
print("--- Converting to datetime ---\n")
data['tpep_pickup_datetime'] = pd.to_datetime(data['tpep_pickup_datetime'])
data['tpep_dropoff_datetime'] = pd.to_datetime(data['tpep_dropoff_datetime'])
data['trip_time'] = data['tpep_dropoff_datetime'] - data['tpep_pickup_datetime']

'''Copying clean data to CSV'''
# print("--- Copying clean data to CSV ---\n")
# data.to_csv("yellow_tripdata_2019-1_V1.csv", index=False)

'''Reading clean data'''
# print("--- Reading clean data ---\n")
# data = pd.read_csv('yellow_tripdata_2019-1_V1.csv')
# print(data.head())
# print(data.dtypes)
# with ProgressBar():
#     min_date = data['tpep_pickup_datetime'].min().compute()
# print(min_date)

'''Converting datetime to unix'''
print("--- Converting datetime to unix time ---\n")
data_unix = data.copy()
data_unix['tpep_pickup_datetime'] = (data_unix['tpep_pickup_datetime'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
data_unix['tpep_dropoff_datetime'] = (data_unix['tpep_dropoff_datetime'] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

print("--- Adding additional attribute combinations ---\n")
data_unix['trip_time'] = data_unix['tpep_dropoff_datetime'] - data_unix['tpep_pickup_datetime']
data_unix['distance/time'] = data_unix['trip_distance'] / data_unix['trip_time'] # lin correlations close zero
print("Unix time data head:\n", data_unix.head())

'''Creating train and test set'''
print("--- Creating train and test set ---\n")
train_set, test_set = train_test_split(data_unix, test_size=0.3, random_state=42)

'''Looking for correlations'''
# print("--- Checking for linear pearsons correlations ---\n")
# corr_matrix = train_set.corr()
# check_fare_amount = corr_matrix['fare_amount'].sort_values(ascending=False)
# print("\nCheck fare amount correlations:\n", check_fare_amount)

'''Throwing out last irrelevant features'''
print("--- Throwing out irrelevant features ---\n")
irrelevant_features = ['RatecodeID', 'payment_type']
data_unix.drop(irrelevant_features, inplace=True, axis=1)

'''Split data'''
print("--- Splitting data ---\n")

predict = 'fare_amount'

X = data_unix.drop([predict], axis=1)
y = data_unix[predict]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

'''Algorithms'''
print("--- Scaling and transforming data ---\n")
numerical_X_train = X_train.drop(['PULocationID', 'DOLocationID'], axis=1)
num_attribs_X_train = list(numerical_X_train)
cat_attribs_X_train = ['PULocationID', 'DOLocationID']

# numerical_X_test = X_test.drop(['PULocationID', 'DOLocationID'], axis=1)
# num_attribs_X_test = list(numerical_X_train)
# cat_attribs_X_test = ['PULocationID', 'DOLocationID']

scale_transform = ColumnTransformer([
                            ('scaler', StandardScaler(), num_attribs_X_train),
                            ('cat', OneHotEncoder(), cat_attribs_X_train)
                        ])

X_train_prepared = scale_transform.fit_transform(X_train)
# X_test_prepared = scale_transform.fit_transform(X_test)

def display_scores(scores):
    print("\nScores:\n", scores)
    print("Mean:\n", scores.mean())
    print("Standard deviation:\n", scores.std())

lin_reg = LinearRegression()

print("\n\tCross validation for Linear Regression:")
lin_reg_scores = cross_val_score(lin_reg, X_train_prepared, y_train, scoring="neg_mean_squared_error", cv=10, n_jobs=-1)
lin_reg_rmse_scores = np.sqrt(-lin_reg_scores)
display_scores(lin_reg_rmse_scores)

# lin_reg.fit(X_train_prepared, y_train)
# predictions = lin_reg.predict(X_test_prepared)

'''Plot outputs'''
# plt.scatter(X_test_prepared, y_test,  color='black', alpha=0.1)
# plt.plot(X_test_prepared, predictions, color='blue', linewidth=3)
# plt.xticks(())
# plt.yticks(())
# plt.show()
