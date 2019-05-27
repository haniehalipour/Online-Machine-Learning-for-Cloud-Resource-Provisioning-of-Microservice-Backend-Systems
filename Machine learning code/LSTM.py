# LSTM tutorial
# https://stackabuse.com/time-series-analysis-with-lstm-using-pythons-keras-library/

#import numpy as np
from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
import pandas as pd
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from pandas import read_csv
from pandas import DataFrame
from pandas import concat
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
 
# convert series to supervised learning
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = DataFrame(data)
	cols, names = list(), list()
	# input sequence (t-n, ... t-1)
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	# forecast sequence (t, t+1, ... t+n)
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	# put it all together
	agg = concat(cols, axis=1)
	agg.columns = names
	# drop rows with NaN values
	if dropnan:
		agg.dropna(inplace=True)
	return agg
 
# load dataset
#dataset = read_csv('pollution.csv', header=0, index_col=0)

'''
def parser(d, t):
	dt = d + " " + t + ":00"
	return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
dataset = read_csv('dataset.csv', header=0, parse_dates={'datetime': ['date', 'time']}, index_col=0, date_parser=parser)

dataset.columns = ['cpu','memory','network_in','network_out','final_target','final_class']
dataset.index.name = 'date'

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range = (0, 99)) #scale "network_in" and "network_out" in 0 to 99
dataset[['network_in','network_out']] = scaler.fit_transform(dataset[['network_in','network_out']])

#"final_class" column is not useful for LSTM, then we will drop it
dataset.drop(columns=['final_class'], inplace=True)
'''
dataset = read_csv('dataset_2.csv', header=0, index_col=None)
dataset.columns = ['cpu','network_in','network_out','memory','final_target']
#dataset.index.name = 'date'

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range = (0, 99)) #scale "network_in" and "network_out" in 0 to 99
dataset[['network_in','network_out']] = scaler.fit_transform(dataset[['network_in','network_out']])

#"final_class" column is not useful for LSTM, then we will drop it
#dataset.drop(columns=['final_class'], inplace=True)





#dataset.drop(columns=['final_target'], inplace=True)
values = dataset.values
#print (values[0])

# integer encode direction
#encoder = LabelEncoder()
#values[:,4] = encoder.fit_transform(values[:,4])

# ensure all data is float
values = values.astype('float32')
# normalize features
#scaler = MinMaxScaler(feature_range=(0, 1))
#scaled = scaler.fit_transform(values)
#print(values[0])
# frame as supervised learning
#reframed = series_to_supervised(scaled, 1, 1)
reframed = series_to_supervised(values, 1, 1)
#print(reframed.shape)
#print(reframed.head())
# drop columns we don't want to predict
reframed.drop(reframed.columns[[5,6,7,8,9]], axis=1, inplace=True)
#print(reframed.shape)
#print(reframed.head())
#print (reframed)
# split into train and test sets
values = reframed.values
#n_train_hours = int(reframed.shape[0] * 0.99)
n_train_hours = reframed.shape[0] - 59
train = values[:n_train_hours, :]
test = values[n_train_hours:, :]
# split into input and outputs
train_X, train_y = train[:, :-1], train[:, -1]
test_X, test_y = test[:, :-1], test[:, -1]
#print (train_X, train_y)

# reshape input to be 3D [samples, timesteps, features]
train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
#print(train_X.shape, train_y.shape, test_X.shape, test_y.shape) #(168, 1, 4) (168,) (72, 1, 4) (72,)
#print (train_X)
#print (train_y)
#exit()
# design network
model = Sequential()
model.add(LSTM(100, input_shape=(train_X.shape[1], train_X.shape[2])))
model.add(Dense(1))
model.compile(loss='mae', optimizer='adam')
model.summary()
#exit()
# fit network
history = model.fit(train_X, train_y, epochs=200, batch_size=128, validation_data=(test_X, test_y), verbose=2, shuffle=False)
# plot history
pyplot.plot(history.history['loss'], label='train')
pyplot.plot(history.history['val_loss'], label='test')
pyplot.legend()
pyplot.show()
pyplot.clf()
#print (history.history['loss'])

# make a prediction
yhat = model.predict(test_X)
print("predicted final_target for {} steps:".format(len(test_y)))
for x in yhat:
	print(x[0])

print("Real final_target for {} steps:".format(len(test_y)))
for x in test_y:
	print(x)
#print (yhat)
#print (test_y)
pyplot.plot(yhat.reshape(-1), label='real')
pyplot.plot(test_y, label='predicted')
pyplot.legend()
pyplot.show()
pyplot.clf()

test_X = test_X.reshape((test_X.shape[0], test_X.shape[2]))
# invert scaling for forecast
inv_yhat = concatenate((yhat, test_X[:, 1:]), axis=1)
#inv_yhat = scaler.inverse_transform(inv_yhat)
inv_yhat = inv_yhat[:,0]
# invert scaling for actual
test_y = test_y.reshape((len(test_y), 1))
inv_y = concatenate((test_y, test_X[:, 1:]), axis=1)
#inv_y = scaler.inverse_transform(inv_y)
inv_y = inv_y[:,0]
# calculate RMSE
rmse = sqrt(mean_squared_error(inv_y, inv_yhat))
print('Test RMSE: %.3f' % rmse)