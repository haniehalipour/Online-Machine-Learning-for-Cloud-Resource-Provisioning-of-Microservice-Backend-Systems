#!/Python36-32/python
import sys
sys.stderr = sys.stdout

#Enable HTML format for default python\s Outputs like Errors
import cgitb
cgitb.enable()#Enable HTML Format

import cgi#Handle GET/POST

#Print HTML header to use as a web-service
print("Content-type: text/html\n\n")

#import time
import math

import datetime
#import tinys3
#import xlsxwriter
#import threading#Timer
import json
import requests
import os
import csv

import random

#Sxikit Liberaries
#import numpy as np
import pandas as pd
from sklearn.externals import joblib
#import pickle
from sklearn.svm import SVC #Multiclass
from sklearn.svm import SVR #SVR
import sklearn.ensemble as ENS
from sklearn import linear_model #Regression
from sklearn.model_selection import cross_val_score

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
start = datetime.datetime.now()
# create the outputs folder
global output_dir
output_dir = './outputs/'
os.makedirs(output_dir, exist_ok=True)

####################################
## Get Predict Data from terminal ##
####################################
#when we are using WebService, We need to handle Data using CGI library
#Data is sent as a GET/POST method
web_req_data = cgi.FieldStorage()
try:
	predict_data = web_req_data["predict"].value
except:
	predict_data = False
'''
#when we are using console (CMD) we need to get passed Data by this way
try:
	predict_data = sys.argv[1]
except:
	predict_data = False
'''

#Reference for Requests liberary:
#http://docs.python-requests.org/en/master/user/quickstart/
restful_api = "https://qstxpu8sn7.execute-api.eastus-azure.com/api/restfull"
#conn = tinys3.Connection('**************','**************************',tls=True)

#################################
## Send Request to RestFul API ##
#################################
def rest_request(req):
	#convert request json to web format (var1=val1&var2=val2&...)
	web_request = json.dumps(req, separators=('&', '=')).replace('{','').replace('}','').replace('"','').replace("'","")
	print ('Request sent to server: {}'.format(web_request))
	###############
	## Set Timer ##
	###############
	#threading.Timer(60.0, rest_request).start()
	
	#r = requests.post(restful_api, data = {'req':'get_name'})
	r = requests.post(restful_api+"/?"+web_request)
	
	if r.status_code == 200:
		resp = json.loads(r.content)
		try:
			if resp["error"]:
				print ("Some Error happened related to requested command.")
				print ("Error is: {}".format(resp["error"]))
		except:
			return resp
	else:
		print ("There is some error with Restful API")
		print ("Response status_code is: {}".format(r.status_code))
	
#rest_request()

########################
## MultiClass Trainer ##
########################
def multiclass_trainer(X, Y, export_name):
	clf = SVC()
	clf.fit(X, Y.values.ravel())
	print ("\nMulticlass model is created with below details:\n{}".format(clf))
	
	model_name = export_name+'_multiclass.pkl'
	joblib.dump(clf, model_name)
	
	scores = cross_val_score(clf, X, Y.values.ravel(), cv=5)
	print (scores)
	print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
	#multiclass_predictor(X[27:57], model_name)
	
###########################
## MultiClass Prediction ##
###########################
def multiclass_predictor (X, model_name):
	clf2 = joblib.load(model_name) 
	print (list(clf2.predict(X)))
	
########################
## Regression Trainer ##
########################
def regression_trainer(X, Y, export_name):
	reg = linear_model.LinearRegression()
	reg.fit(X, Y.values.ravel())
	print ("\nRegression model is created with below details:\n{}".format(reg))
	
	model_name = export_name+'_regression.pkl'
	joblib.dump(reg, model_name)
	
	print ("Start Cross Validation")
	scores = cross_val_score(reg, X, Y.values.ravel(), cv=5)
	print (scores)
	print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
	#regression_predictor(X[27:57], model_name)

###########################
## Regression Prediction ##
###########################
def regression_predictor (X, model_name):
	reg2 = joblib.load(model_name) 
	print (list(reg2.predict(X)))
	

	
	
	
	
	
	
####################################
## LR (Linear Regression) Trainer ##
####################################
def LR_trainer(X, Y, export_name):
	a = datetime.datetime.now()
	#params = {'fit_intercept': False, 'normalize': True, }
	clf = linear_model.LinearRegression()
	clf.fit(X, Y.values.ravel())
	print ("\nLR (Linear Regression) model is created with below details:\n{}".format(clf))
	
	model_name = output_dir+export_name+'_LR.pkl'
	joblib.dump(clf, model_name)
	
	'''print ("Start Cross Validation")
	scores = cross_val_score(clf, X, Y.values.ravel(), cv=5)
	print (scores)
	print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
	'''
	
	#########################
	## Mean Absolute Error ##
	#########################
	y_pred = clf.predict(X)
	MAE = mean_absolute_error(Y, y_pred)
	MSE = mean_squared_error(Y, y_pred)
	RMSE = math.sqrt(mean_squared_error(Y, y_pred))
	R2 = r2_score(Y, y_pred, multioutput='variance_weighted')
	
	print ("LR Mean Absolute Error: {}".format(MAE))
	print ("LR Mean Squared Error: {}".format(MSE))
	print ("LR Root Mean Squared Error: {}".format(RMSE))
	print ("LR R^2 (coefficient of determination) regression score: {}".format(R2))
	
	winner_model = MAE + MSE + RMSE + (1-R2)
	print ("MAE + MSE + RMSE + (1-R2) = {}".format(winner_model))
	#Export Prediction To CSV
	pd.DataFrame(y_pred, columns=['Linear Regression']).to_csv(output_dir+'LR_Predicted.csv')
	print("Only LR Creation time: {}".format(datetime.datetime.now() - a))
	print ("Total LR Creation Time: {}".format(datetime.datetime.now() - start))
	#LR_predictor(X[27:28], model_name)#X[27:28] mean row 27 of dataset

#######################################
## LR (Linear Regression) Prediction ##
#######################################
def LR_predictor (X, model_name):
	clf = joblib.load(model_name)
	print ("Regression: {}".format(clf.predict(X)[0]))
	
#####################################
## SVR (Support Vector Regression) ##
#####################################
#http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
def SVR_trainer(X, Y, export_name):
	a = datetime.datetime.now()
	clf = SVR(C=100)
	clf.fit(X, Y.values.ravel())
	print ("\nSVR (Support Vector Regression) model is created with below details:\n{}".format(clf))
	
	model_name = output_dir+export_name+'_svr.pkl'
	joblib.dump(clf, model_name)
	
	'''print ("Start Cross Validation")
	scores = cross_val_score(clf, X, Y.values.ravel(), cv=5)
	print (scores)
	print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
	'''
	#########################
	## Mean Absolute Error ##
	#########################
	y_pred = clf.predict(X)
	MAE = mean_absolute_error(Y, y_pred)
	MSE = mean_squared_error(Y, y_pred)
	RMSE = math.sqrt(mean_squared_error(Y, y_pred))
	R2 = r2_score(Y, y_pred, multioutput='variance_weighted')
	
	print ("SVR Mean Absolute Error: {}".format(MAE))
	print ("SVR Mean Squared Error: {}".format(MSE))
	print ("SVR Root Mean Squared Error: {}".format(RMSE))
	print ("SVR R^2 (coefficient of determination) regression score: {}".format(R2))
	
	winner_model = MAE + MSE + RMSE + (1-R2)
	print ("MAE + MSE + RMSE + (1-R2) = {}".format(winner_model))
	#Export Prediction To CSV
	pd.DataFrame(y_pred, columns=['Support Vector Regression']).to_csv(output_dir+'SVR_Predicted.csv')
	print("Only SVR Creation time: {}".format(datetime.datetime.now() - a))
	print ("Total SVR Creation Time: {}".format(datetime.datetime.now() - start))
	#SVR_predictor(X[27:28], model_name)#X[27:28] mean row 27 of dataset

################################################
## SVR (Support Vector Regression) Prediction ##
################################################
def SVR_predictor (X, model_name):
	clf = joblib.load(model_name)
	print ("SVR: {}".format(clf.predict(X)[0]))
	
#######################################
## GBR (Gradient Boosting Regressor) ##
#######################################
#http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html
#http://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_regression.html
def GBR_trainer(X, Y, export_name):
	a = datetime.datetime.now()
	params = {'n_estimators': 500, 'max_depth': 100, 'min_samples_split': 2, 'learning_rate': 0.1, 'loss': 'ls'}#LAD,HUBER,QUANTILE
	clf = ENS.GradientBoostingRegressor(**params)
	clf.fit(X, Y.values.ravel())
	print ("\nGBR (Gradient Boosting Regressor) model is created with below details:\n{}".format(clf))
	
	model_name = output_dir+export_name+'_GBR.pkl'
	joblib.dump(clf, model_name)
	
	'''print ("Start Cross Validation")
	scores = cross_val_score(clf, X, Y.values.ravel(), cv=5)
	print (scores)
	print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
	'''
	#########################
	## Mean Absolute Error ##
	#########################
	y_pred = clf.predict(X)
	MAE = mean_absolute_error(Y, y_pred)
	MSE = mean_squared_error(Y, y_pred)
	RMSE = math.sqrt(mean_squared_error(Y, y_pred))
	R2 = r2_score(Y, y_pred, multioutput='variance_weighted')
	
	print ("GBR Mean Absolute Error: {}".format(MAE))
	print ("GBR Mean Squared Error: {}".format(MSE))
	print ("GBR Root Mean Squared Error: {}".format(RMSE))
	print ("GBR R^2 (coefficient of determination) regression score: {}".format(R2))
	
	winner_model = MAE + MSE + RMSE + (1-R2)
	print ("MAE + MSE + RMSE + (1-R2) = {}".format(winner_model))
	#Export Prediction To CSV
	pd.DataFrame(y_pred, columns=['Gradient Boosting Regressor']).to_csv(output_dir+'GBR_Predicted.csv')
	print("Only GBR Creation time: {}".format(datetime.datetime.now() - a))
	print ("Total GBR Creation Time: {}".format(datetime.datetime.now() - start))
	#GBR_predictor(X[27:28], model_name)#X[27:28] mean row 27 of dataset

##################################################
## GBR (Gradient Boosting Regressor) Prediction ##
##################################################
def GBR_predictor (X, model_name):
	clf = joblib.load(model_name)
	print ("GBR: {}".format(clf.predict(X)[0]))
	
	
	
	
	
	
	
	
	
	
	

####################
## Start Training ##
####################
def train():
	#################################
	## Request Dataset information ##
	#################################
	info = rest_request({'req':'system_dataset_info'})
	'''
	{'type': 'csv', 'name': 'scikit', 'has_header_row': 'yes', 'train_columns': [{'col_name': 'CPUUtilization_Average', 'col_number': '2'}, {'col_name': 'CPUUtilization_Target', 'col_number': '3'}, {'col_name': 'NetworkIn_Average', 'col_number': '4'}, {'col_name': 'NetworkIn_Target', 'col_number': '5'}, {'col_name': 'NetworkOut_Average', 'col_number': '6'}, {'col_name': 'NetworkOut_Target', 'col_number': '7'}, {'col_name': 'MemoryUtilization_Average', 'col_number': '8'}, {'col_name': 'MemoryUtilization_Target', 'col_number': '9'}], 'multiclass_target_col': {'col_name': 'Final_Class', 'col_number': '11'}, 'regression_target_col': {'col_name': 'Final_Target', 'col_number': '10'}, 'export_model_name': 'ski_model'}
	'''
	input_file = info['name']+"."+info['type']
	'''
	######################
	## Get Dataset File ##
	######################
	dataset_content = ""
	print ('Request to get Dataset file "'+input_file+'" from multiple-targets (S3)')
	dataset_file = requests.get('https://s3.amazonaws.com/multiple-targets/export_to_csv/'+input_file)
	if dataset_file.status_code == 200 and len(dataset_file.content) > 0:
		print ('Load "'+input_file+'"')
		dataset_content = dataset_file.content
		#print (dataset_content)
	else:
		print ("Error {} happened".format(dataset_file.status_code))
	'''
	#############################################
	## Create temporary file of loaded dataset ##
	#############################################
	loaded_dataset = 'loaded_dataset.csv'
	'''file = open(loaded_dataset,'wb')
	file.write(dataset_content)
	file.close()
	'''
	######################
	## Create DataFrame ##
	######################
	df = pd.read_csv(loaded_dataset)
	#original_headers = list(df.columns.values)
	#print ("\nSelected Headers to train:\n{}".format(original_headers))
	train_headers = []
	multiclass_target = regression_target = ""
	
	for col in info['train_columns']:
		if info['has_header_row'] == 'yes':
			#our dataset has header row (first row is header)
			train_headers.append(col['col_name'])
			multiclass_target = info['multiclass_target_col']['col_name']
			regression_target = info['regression_target_col']['col_name']
		else:
			#there is no header name
			train_headers.append(col['col_number'])
			multiclass_target = info['multiclass_target_col']['col_number']
			regression_target = info['regression_target_col']['col_number']
	
	X = df[train_headers].copy()
	Y_multiclass = df[[multiclass_target]].copy()
	Y_regression = df[[regression_target]].copy()
	
	#multiclass_trainer(X, Y_multiclass, info['export_model_name'])
	#regression_trainer(X, Y_regression, info['export_model_name'])
	LR_trainer(X, Y_regression, info['export_model_name'])
	SVR_trainer(X, Y_regression, info['export_model_name'])
	GBR_trainer(X, Y_regression, info['export_model_name'])
	
	###################################
	## Remove temporary dataset file ##
	###################################
	#os.remove(loaded_dataset)
	    
	print ("Total Time: {}".format(datetime.datetime.now() - start))

#########################
## Realtime Prediction ##
#########################
if predict_data:
	#If there is some data to predict, do prediction
	info = rest_request({'req':'system_export_model_name'})
	
	predict_data = "["+predict_data+"]"
	meta_record = predict_data[1:-1].split(',')
	records = []
	for item in meta_record:
		records.append(float(item))
		
	print("Predicting:")
	#multiclass_predictor ([records], info['export_model_name']+'_multiclass.pkl')
	#regression_predictor ([records], info['export_model_name']+'_regression.pkl')
	LR_predictor ([records], info['export_model_name']+'_LR.pkl')
	SVR_predictor ([records], info['export_model_name']+'_SVR.pkl')
	GBR_predictor ([records], info['export_model_name']+'_GBR.pkl')
else:
	#there isn't any data to predict.
	#then start training
	train()
exit()