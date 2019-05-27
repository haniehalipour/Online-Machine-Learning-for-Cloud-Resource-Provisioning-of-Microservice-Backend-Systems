###!/Python36-32/python
import sys
sys.stderr = sys.stdout
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_pdf import PdfPages

#Enable HTML format for default python\s Outputs like Errors
import cgitb
#cgitb.enable()#Enable HTML Format

import cgi#Handle GET/POST

#Print HTML header to use as a web-service
print("Content-type: text/html\n\n")

#import time
import math

import time
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
from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
start = datetime.datetime.now()
# create the outputs folder
global output_dir
output_dir = ''
#os.makedirs(output_dir, exist_ok=True)

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
restful_api = "https://qstxpu8sn7.execute-api.us-east-1.amazonaws.com/api/restfull"
#conn = tinys3.Connection('*************',tls=True)

#################################
## Send Request to RestFul API ##
#################################
def rest_request(req):
	manual_api = '{"type": "csv", "name": "17-12-16-20-03-17", "has_header_row": "yes", "train_columns": [{"col_name": "CPUUtilization_Average", "col_number": "2"}, {"col_name": "NetworkIn_Average", "col_number": "4"}, {"col_name": "NetworkOut_Average", "col_number": "6"}, {"col_name": "MemoryUtilization_Average", "col_number": "8"}], "multiclass_target_col": {"col_name": "Final_Class", "col_number": "11"}, "regression_target_col": {"col_name": "Final_Target", "col_number": "10"}, "export_model_name": "ski_model"}'
	return json.loads(manual_api)
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

####################################
## LR (Linear Regression) Trainer ##
####################################
#http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
def LR_trainer(X, Y, test, export_name):
	a = datetime.datetime.now()
	#params = {'fit_intercept': False, 'normalize': True, }
	params = {}
	clf = linear_model.LinearRegression()
	
	X_train = X_test = X
	y_train = y_test = Y
	
	if test > 0:
		#we want to test
		X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test, shuffle=False)
	
	clf.fit(X_train, y_train.values.ravel())
	print ("\nLR (Linear Regression) model is created with below details:\n{}".format(clf))
	
	model_name = output_dir+export_name+'_LR.pkl'
	joblib.dump(clf, model_name)
	
	'''print ("Start Cross Validation")
	scores = cross_val_score(clf, X, Y.values.ravel(), cv=5)
	print (scores)
	print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
	'''
	
	##################
	## Error Scores ##
	##################
	y_pred = clf.predict(X_test)
	scores = {'MAE':mean_absolute_error(y_test, y_pred), 'MSE':mean_squared_error(y_test, y_pred), 'RMSE':math.sqrt(mean_squared_error(y_test, y_pred)), 'R2':r2_score(y_test, y_pred)}
	
	#all_scores.append({"C": C, "Epsilon": Epsilon, "Score":scores})
	
	scores_as_title = ""
	temp_index = 1;
	for index in scores:
		scores_as_title += index + ": " + str(scores[index]) + " - "
		if temp_index % 2 == 0:
			scores_as_title += "\n"
		temp_index += 1
	
	Sorted_X_test = X_test.sort_index(axis=0)
	plt.plot(Sorted_X_test[:100].index.values, y_test[:100].to_dict(orient='list')['Final_Target'], label='True data')
	plt.plot(Sorted_X_test[:100].index.values, y_pred[:100], 'co', label='LR | {}'.format(params))
	#plt.plot(X_test[1::2], pred_lm[1::2], 'mo', label='Linear Reg')
	plt.legend(loc='lower right');
	plt.title(scores_as_title, fontsize="10", color="black")
	export_name = 'LR_{}.png'.format(time.time())
	plt.savefig("./LR/"+export_name, dpi=199)
	#plt.show()
	plt.clf()
	
	print("Only LR Creation time: {}".format(datetime.datetime.now() - a))
	print ("Total LR Creation Time: {}".format(datetime.datetime.now() - start))
	
	#y_pred[1] = y_test
	#y_pred.merge(pd.DataFrame(data = [y_test.values] * len(y_test), columns = y_test.index))
	f= open("LR_Predicted_result.csv","w+")
	f.write("Real,Predicted\n")
	y_test_array = y_test.to_dict(orient='list')['Final_Target'];
	for idx, val in enumerate(y_pred):
		f.write("{},{}\n".format(y_test_array[idx], val))

	#print(y_test.to_dict(orient='list')['Final_Target'][0])
	
	#pd.DataFrame(y_pred, columns=['real', 'Linear Regression']).to_csv('LR_Predicted.csv')
	#LR_predictor(X[27:28], model_name)#X[27:28] mean row 27 of dataset

#######################################
## LR (Linear Regression) Prediction ##
#######################################
def LR_predictor (X, model_name):
	a = datetime.datetime.now()
	
	clf = joblib.load(model_name)
	print ("Regression: {}".format(clf.predict(X)[0]))
	
	print ("Only LR_predictor time: {}".format(datetime.datetime.now() - a))
	print ("Total LR_predictor Time: {}".format(datetime.datetime.now() - start))
	
#####################################
## SVR (Support Vector Regression) ##
#####################################
#http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
def SVR_trainer_sharpeddddddddd(X, Y, export_name):
	params = {'C': 1, 'kernel': 'linear'}
	clf = SVR(**params)
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
	print ("SVR Mean Absolute Error: {}".format(mean_absolute_error(Y, y_pred)))
	print ("SVR Mean Squared Error: {}".format(mean_squared_error(Y, y_pred)))
	print ("SVR Root Mean Squared Error: {}".format(math.sqrt(mean_squared_error(Y, y_pred))))
	print ("SVR R^2 (coefficient of determination) regression score: {}".format(r2_score(Y, y_pred)))
	#Export Prediction To CSV
	pd.DataFrame(y_pred, columns=['Support Vector Regression']).to_csv('SVR_Predicted.csv')
	#print ()
	#print (Y.index.values)
	#SVR_predictor(X[27:57], model_name)
	plt.plot(Y[450:500].index.values,Y[450:500].to_dict(orient='list')['Final_Target'], label='True data')
	plt.plot(X[450:500].index.values, y_pred[450:500], 'co', label='SVR | {}'.format(params))
	#plt.plot(X_test[1::2], pred_lm[1::2], 'mo', label='Linear Reg')
	plt.legend(loc='lower right');
	#plt.show()
	#pp = PdfPages('multipage.pdf')
	
	export_name = 'svr_' + str(time.time()) +'.png'
	plt.savefig(export_name)
	#pp.savefig()
	
#####################################
## SVR (Support Vector Regression) ##
#####################################
#http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
def SVR_trainer(X, Y, test, export_name):
	a = datetime.datetime.now()
	#c_range = {1, 20, 40, 60, 80}
	#epsilon_range = {0.1, 0.01, 0.001, 0.0001, 0.00001}
	c_range = {40}
	epsilon_range = {0.001}
	
	all_scores = []
	
	for C in c_range:
		for Epsilon in epsilon_range:
			params = {'C': C, 'epsilon': Epsilon, 'kernel': 'linear'}
			clf = SVR(**params)
			
			X_train = X_test = X
			y_train = y_test = Y
			
			if test > 0:
				#we want to test
				X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test, shuffle=True)
			
			clf.fit(X_train, y_train.values.ravel())
			#print ("\nSVR (Support Vector Regression) model is created with below details:\n{}".format(clf))
			
			#model_name = output_dir+export_name+'_svr.pkl'
			#joblib.dump(clf, model_name)
			
			##################
			## Error Scores ##
			##################
			y_pred = clf.predict(X_test)
			scores = {'MAE':mean_absolute_error(y_test, y_pred), 'MSE':mean_squared_error(y_test, y_pred), 'RMSE':math.sqrt(mean_squared_error(y_test, y_pred)), 'R2':r2_score(y_test, y_pred)}
			
			all_scores.append({"C": C, "Epsilon": Epsilon, "Score":scores})
			
			scores_as_title = ""
			temp_index = 1;
			for index in scores:
				scores_as_title += index + ": " + str(scores[index]) + " - "
				if temp_index % 2 == 0:
					scores_as_title += "\n"
				temp_index += 1
			
			Sorted_X_test = X_test.sort_index(axis=0)
			plt.plot(Sorted_X_test[:100].index.values, y_test[:100].to_dict(orient='list')['Final_Target'], label='True data')
			plt.plot(Sorted_X_test[:100].index.values, y_pred[:100], 'co', label='SVR | {}'.format(params))
			#plt.plot(X_test[1::2], pred_lm[1::2], 'mo', label='Linear Reg')
			plt.legend(loc='lower right');
			plt.title(scores_as_title, fontsize="10", color="black")
			export_name = 'svr_C_{}__Epsilon_{}_{}.png'.format(C, Epsilon, time.time())
			plt.savefig("./SVR/"+export_name, dpi=199)
			#plt.show()
			plt.clf()
			time.sleep(1)
	
	with open('SVR_Scores.csv','w') as file:
		file.write("C, Epsilon, MAE, MSE, RMSE, R2")
		file.write('\n')
		
		for row in all_scores:
			temp_report = "{}, {}, {}, {}, {}, {}".format(row["C"], row["Epsilon"], row["Score"]["MAE"], row["Score"]["MSE"], row["Score"]["RMSE"], row["Score"]["R2"])
			#print(row)
			#print()
			file.write(temp_report)
			file.write('\n')
			
	print("Only SVR Creation time: {}".format(datetime.datetime.now() - a))
	print ("Total SVR Creation Time: {}".format(datetime.datetime.now() - start))
	
	f= open("SVR_Predicted_result.csv","w+")
	f.write("Real,Predicted\n")
	y_test_array = y_test.to_dict(orient='list')['Final_Target'];
	for idx, val in enumerate(y_pred):
		f.write("{},{}\n".format(y_test_array[idx], val))
	
	#SVR_predictor(X[27:28], model_name)#X[27:28] mean row 27 of dataset

################################################
## SVR (Support Vector Regression) Prediction ##
################################################
def SVR_predictor (X, model_name):
	a = datetime.datetime.now()

	clf = joblib.load(model_name)
	print ("SVR: {}".format(clf.predict(X)[0]))
	
	print ("Only SVR_predictor time: {}".format(datetime.datetime.now() - a))
	print ("Total SVR_predictor Time: {}".format(datetime.datetime.now() - start))
	
#######################################
## GBR (Gradient Boosting Regressor) ##
#######################################
#http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html
#http://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_regression.html
def GBR_trainer(X, Y, test, export_name):
	a = datetime.datetime.now()
	n_estimator_range = {10,100,500,1000}
	max_depth_range = {3,4,5,6,7}
	learning_rate_range = {0.1,0.5,1,2}
	min_samples_split_range = {2,4,8}
	
	all_scores = []
	
	for n_estimator in n_estimator_range:
		for max_depth in max_depth_range:
			for learning_rate in learning_rate_range:
				for min_samples_split in min_samples_split_range:
					params = {'loss':'ls', 'learning_rate':learning_rate, 'n_estimators':n_estimator, 'subsample':1.0, 'criterion':'friedman_mse', 'min_samples_split':min_samples_split, 'min_samples_leaf':1, 'min_weight_fraction_leaf':0.0, 'max_depth':max_depth, 'min_impurity_decrease':0.0, 'min_impurity_split':None, 'init':None, 'random_state':None, 'max_features':None, 'alpha':0.9, 'max_leaf_nodes':None, 'warm_start':False, 'presort':'auto'}
					
					clf = ENS.GradientBoostingRegressor(**params)
					
					X_train = X_test = X
					y_train = y_test = Y
					
					if test > 0:
						#we want to test
						X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test, shuffle=True)
					
					#clf.fit(X, Y.values.ravel())
					clf.fit(X_train, y_train.values.ravel())
					#print ("\nGBR (Gradient Boosting Regressor) model is created with below details:\n{}".format(clf))
					
					#model_name = output_dir+export_name+'_GBR.pkl'
					#joblib.dump(clf, model_name)
					
					'''print ("Start Cross Validation")
					scores = cross_val_score(clf, X, Y.values.ravel(), cv=5)
					print (scores)
					print ("Accuracy: {} (+/- {})".format(scores.mean(), scores.std() * 2))
					'''
					##################
					## Error Scores ##
					##################
					y_pred = clf.predict(X_test)
					
					scores = {'MAE':mean_absolute_error(y_test, y_pred), 'MSE':mean_squared_error(y_test, y_pred), 'RMSE':math.sqrt(mean_squared_error(y_test, y_pred)), 'R2':r2_score(y_test, y_pred)}
					all_scores.append({"n_estimator": n_estimator, "max_depth": max_depth, "learning_rate": learning_rate, "min_samples_split": min_samples_split, "Score":scores})
					
					scores_as_title = ""
					temp_index = 1;
					for index in scores:
						scores_as_title += index + ": " + str(scores[index]) + " - "
						if temp_index % 2 == 0:
							scores_as_title += "\n"
						temp_index += 1
						
					#Export Prediction To CSV
					#pd.DataFrame(y_pred, columns=['Gradient Boosting Regressor']).to_csv('GBR_Predicted.csv')
					#GBR_predictor(X[27:57], model_name)
					Sorted_X_test = X_test.sort_index(axis=0)
					plt.plot(Sorted_X_test[:100].index.values, y_test[:100].to_dict(orient='list')['Final_Target'], label='True data')
					params = json.dumps(params)
					params = params[:200] + "\n" + params[200:]
					plt.plot(Sorted_X_test[:100].index.values, y_pred[:100], 'co', label='GBR | {}'.format(params))
					#plt.plot(X_test[1::2], pred_lm[1::2], 'mo', label='Linear Reg')
					plt.legend(loc='lower right', fontsize="3.5");
					plt.title(scores_as_title, fontsize="10", color="black")
					export_name = 'GBR_ne_{}__md_{}__lr_{}__mss_{}_{}.png'.format(n_estimator, max_depth, learning_rate, min_samples_split, time.time())
					plt.savefig("./GBR/"+export_name, dpi=199)
					#plt.show()
					plt.clf()
					time.sleep(0.5)
	
	with open('GBR_Report.csv','w') as file:
		file.write("n_estimator, max_depth, learning_rate, min_samples_split, MAE, MSE, RMSE, R2")
		file.write('\n')
		
		for row in all_scores:
			temp_report = "{}, {}, {}, {}, {}, {}, {}, {}".format(row["n_estimator"], row["max_depth"], row["learning_rate"], row["min_samples_split"], row["Score"]["MAE"], row["Score"]["MSE"], row["Score"]["RMSE"], row["Score"]["R2"])
			#print(row)
			#print()
			file.write(temp_report)
			file.write('\n')
	#return scores
	
	print("Only GBR Creation time: {}".format(datetime.datetime.now() - a))
	print ("Total GBR Creation Time: {}".format(datetime.datetime.now() - start))
	
	f= open("GBR_Predicted_result.csv","w+")
	f.write("Real,Predicted\n")
	y_test_array = y_test.to_dict(orient='list')['Final_Target'];
	for idx, val in enumerate(y_pred):
		f.write("{},{}\n".format(y_test_array[idx], val))

##################################################
## GBR (Gradient Boosting Regressor) Prediction ##
##################################################
def GBR_predictor (X, model_name):
	a = datetime.datetime.now()
	
	clf = joblib.load(model_name)
	print ("GBR: {}".format(clf.predict(X)[0]))
	
	print("Only GBR_predictor time: {}".format(datetime.datetime.now() - a))
	print ("Total GBR_predictor Time: {}".format(datetime.datetime.now() - start))

####################
## Start Training ##
####################
def train():
	#################################
	## Request Dataset information ##
	#################################
	#info = rest_request({'req':'system_dataset_info'})
	'''
	{'type': 'csv', 'name': 'scikit', 'has_header_row': 'yes', 'train_columns': [{'col_name': 'CPUUtilization_Average', 'col_number': '2'}, {'col_name': 'CPUUtilization_Target', 'col_number': '3'}, {'col_name': 'NetworkIn_Average', 'col_number': '4'}, {'col_name': 'NetworkIn_Target', 'col_number': '5'}, {'col_name': 'NetworkOut_Average', 'col_number': '6'}, {'col_name': 'NetworkOut_Target', 'col_number': '7'}, {'col_name': 'MemoryUtilization_Average', 'col_number': '8'}, {'col_name': 'MemoryUtilization_Target', 'col_number': '9'}], 'multiclass_target_col': {'col_name': 'Final_Class', 'col_number': '11'}, 'regression_target_col': {'col_name': 'Final_Target', 'col_number': '10'}, 'export_model_name': 'ski_model'}
	'''
	info = {'type': 'csv', 'name': 'scikit', 'has_header_row': 'yes', 'train_columns': [{'col_name': 'CPUUtilization_Average', 'col_number': '0'}, {'col_name': 'NetworkIn_Average', 'col_number': '1'}, {'col_name': 'NetworkOut_Average', 'col_number': '2'}, {'col_name': 'MemoryUtilization_Average', 'col_number': '3'}], 'multiclass_target_col': {'col_name': 'Final_Class', 'col_number': '5'}, 'regression_target_col': {'col_name': 'Final_Target', 'col_number': '4'}, 'export_model_name': 'ski_model'}
	input_file = info['name']+"."+info['type']
	
	######################
	## Get Dataset File ##
	######################
	'''dataset_content = ""
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
	
	split_to_test = 0.005
	#multiclass_trainer(X, Y_multiclass, info['export_model_name'])
	#LR_trainer(X, Y_regression, split_to_test, info['export_model_name'])
	SVR_trainer(X, Y_regression, split_to_test, info['export_model_name'])
	#GBR_trainer(X, Y_regression, split_to_test, info['export_model_name'])
	
	###################################
	## Remove temporary dataset file ##
	###################################
	#os.remove(loaded_dataset)

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
	#multiclass_predictor ([records], info['export_model_name']+'_MC.pkl')
	#LR_predictor ([records], info['export_model_name']+'_LR.pkl')
	#SVR_predictor ([records], info['export_model_name']+'_SVR.pkl')
	#GBR_predictor ([records], info['export_model_name']+'_GBR.pkl')
else:
	#there isn't any data to predict.
	#then start training
	train()
exit()
