#import required packages
import pandas as pd
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

#from pandas import DataFrame
from pandas import read_csv
import math
from pandas import datetime
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
#%matplotlib inline

#read the dataset
#df = pd.read_csv("ready_dataset.csv", parse_dates=['date'])
'''
def parser(d):
	return datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
dataset = pd.read_csv('ready_dataset.csv', header=0, parse_dates=['date'], index_col=0, date_parser=parser)
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


#df['Date_Time'] = df.date
#dataset = df.drop(['date'], axis=1)
#dataset.index = df.Date_Time

#check the dtypes
#print(dataset.dtypes)
cols = dataset.columns
#print(cols)

#creating the train and validation set
#train = dataset[:int(0.95*(len(dataset)))]
train = dataset[:len(dataset)-60]
#valid = dataset[int(0.95*(len(dataset))):]
valid = dataset[len(dataset)-60:]

#fit the model
from statsmodels.tsa.vector_ar.var_model import VAR

model = VAR(endog=train)
model_fit = model.fit()

compare_prediction_result = []
print("Real final_target for {} steps".format(valid.shape[0]))
for x in valid['final_target'].values:
	print (x)
	
# make prediction on validation
prediction = model_fit.forecast(model_fit.y, steps=len(valid))
	
#converting predictions to dataframe
pred = pd.DataFrame(index=range(0,len(prediction)),columns=[cols])
for j in range(0,len(cols)):
    for i in range(0, len(prediction)):
       pred.iloc[i][j] = prediction[i][j]
	   
print("Predicted final_target for {} steps".format(pred.shape[0]))
for x in pred['final_target'].values:
	print (x[0])
	
real_final_targets = valid['final_target'].values
predicted_final_targets = pred['final_target'].values
f= open("VAR_compare_result.csv","w+")
f.write("Real,Predicted\n")
for idx, val in enumerate(real_final_targets):
	f.write("{},{}\n".format(real_final_targets[idx], predicted_final_targets[idx][0]))
	
#check rmse
for i in cols:
    print('rmse value for', i, 'is : ', math.sqrt(mean_squared_error(pred[i], valid[i])))
	
#make final predictions
model = VAR(endog=dataset)
model_fit = model.fit()
yhat = model_fit.forecast(model_fit.y, steps=10)
for res in yhat:
	print (res)