import boto3
import json
import xml.etree.ElementTree as ET #https://docs.python.org/3/library/xml.etree.elementtree.html

import time
import datetime
import math
import os
import io
import csv
import subprocess
import sys
#import paramiko
from botocore.vendored import requests
import random

#######################
## Declare Variables ##
#######################
current_api = 'https://xb9p15z5mc.execute-api.us-east-1.amazonaws.com/beta/controller-api'
ml_api = 'http://34.204.71.157/api/'
grafana_API = 'http://34.238.174.246:3000/api/datasources/proxy/1/api/v1/query_range?query='
add_remove_resources_api = 'http://34.204.71.157/api/'
NdbenchAPI = 'http://18.209.34.140:8080/' #http://ec2-35-153-133-46.compute-1.amazonaws.com:8080/
bucket = 'multiple-targets'
dataset_blobName = 'dataset.csv'
dataset_config_blobName = 'dataset_config.json'
ML_model_config_file_name = 'ML_model.json'

dynamodb_table_name = 'api-controller'
# host_ip is the IP of DevOps Instance
host_ip = '52.55.200.37'

def db (do, data):
	#dynamodb_table_name = 'api-controller'
	dynamodb = boto3.resource('dynamodb')
	dynamodb_client = boto3.client('dynamodb')
	existing_tables = dynamodb_client.list_tables()['TableNames']
	
	if dynamodb_table_name not in existing_tables:
		
		table = dynamodb.create_table(
			TableName=dynamodb_table_name,
				KeySchema=[
					{
						'AttributeName': 'field_name',
						'KeyType': 'HASH'  #Partition key
					},
					{
						'AttributeName': 'hack',
						'KeyType': 'RANGE'  #Sort key
					}
				],
				AttributeDefinitions=[
					{
						'AttributeName': 'field_name',
						'AttributeType': 'S'
					},
					{
						'AttributeName': 'hack',
						'AttributeType': 'S'
					}

				],
				ProvisionedThroughput={
					'ReadCapacityUnits': 10,
					'WriteCapacityUnits': 10
				}
			)
			
		print("DynamoDB is creating. please try again one minute later.")
		table.meta.client.get_waiter('table_exists').wait(TableName=dynamodb_table_name)
		#return '{"error":"DynamoDB is creating. please try again one minute later."}'
		
	table = dynamodb.Table(dynamodb_table_name)
	print ("table##########")
	print (table)
	print ("table##########")
	data = json.loads(data)
	
	if do == 'get':
		#get "data['name']" from the database
		response = table.get_item(
			Key={
				'field_name': data['field_name'],
				'hack': 'dynamodb'
			}
		)
		try:
			return response['Item']['field_value']
		except:
			return False
	
	if do == 'insert':
		#insert "data['name'] with data['value']" into the database
		table.put_item(
		   Item={
				'field_name': data['field_name'],
				'hack': 'dynamodb',
				'field_value': data['field_value']
			}
		)
		return True
		
	if do == 'update':
		#update data['value'] for data['name'] into the database
		table.update_item(
			Key={
				'field_name': data['field_name'],
				'hack': 'dynamodb'
			},
			UpdateExpression='SET field_value = :val1',
			ExpressionAttributeValues={
				':val1': data['field_value']
			}
		)
		return True
		
	if do == 'delete':
		#update data['value'] for data['name'] into the database
		table.delete_item(
			Key={
				'field_name': data['field_name'],
				'hack': 'dynamodb'
			}
		)
		return True
		
	return False

#related to this topic we can use "queryStringParameters"
#https://stackoverflow.com/questions/31329958/how-to-pass-a-querystring-or-route-parameter-to-aws-lambda-from-amazon-api-gatew

'''def respond(err, res=None):
	return {
		'statusCode': '400' if err else '200',
		'body': err.message if err else json.dumps(res),
		'headers': {
			'Content-Type': 'application/json',
			"Access-Control-Allow-Origin": "*"
		},
	}
'''

def respond (code, message):
	return {
		"statusCode": code,
		"headers": {
			"Content-Type": 'text/html',
			"Access-Control-Allow-Origin": "*"
		},
		"body": json.dumps(message)
	}
	
ec2 = boto3.resource('ec2')
	
def lambda_handler(event, context):
	operation = event['httpMethod']
	#return respond(200, event)
	#return 'Hello from Lambda'
	
	if operation == 'POST' or operation == 'GET':
		try:
			task = event['queryStringParameters']['task']
		except:
			task = 'no-task'
			
		if task == 'no-task':
			return respond(200, {"message": "there is no 'task' parameter in your request..! Send your request using json format via GET or POST method: {'task'='YOUR-REQUEST-NAME'}"})
		else:
			if task == 'build_model':
				###################
				## Configuration ##
				###################
				for_last_n_minutes = 10
				try:
					for_last_n_minutes = int(event['queryStringParameters']['for_last_n_minutes'])
				except:
					#for_last_n_minutes is not passed by GET or POST
					print ('using default "{}" minutes for_last_n_minutes'.format(for_last_n_minutes))
				
				############################
				## SET START AND END TIME ##
				############################
				#we need to set time period in "timestamp" format
				date = time.time()
				#set "end_time" to one minute ago to make sure that metrics are collected
				#then "end_time" is current time minus one minute
				end_time = math.floor(date) - 60
				#we want to collect metrics for 10 minutes.
				#then "start_time" will be end_time - 10minutes
				start_time = end_time - (for_last_n_minutes * 60)
				
				last_recent_retrieved_time = db('get','{"field_name": "last_recent_retrieved_time"}')
				
				if last_recent_retrieved_time:
					last_recent_retrieved_time = int(last_recent_retrieved_time)
					'''
					if (last_recent_retrieved_time - start_time) > 0:
						#seems the start_time is less than recently retrieved
						#we don't want to add duplicate metrics into the Dataset
						#then we will move start_time to last recent retrieved time + 1 minute
						start_time = last_recent_retrieved_time + 60;
					'''
					start_time = last_recent_retrieved_time + 60;
				
				if (end_time - start_time) < 0:
					time.sleep(((end_time - start_time) * -1) + 61)
					date = time.time()
					end_time = math.floor(date)
					
				print ("Start Time:{}, End Time:{}".format(start_time, end_time))
				collected_metrics = get_metrics (start_time, end_time, grafana_API)
				normilized_dataset = normilize (collected_metrics)
				print('dataset is normilized now')
				
				uploaded_dataset_config_url = upload_dataset (normilized_dataset, bucket, dataset_blobName, dataset_config_blobName)
				
				result = db('insert','{"field_name": "last_recent_retrieved_time", "field_value": "'+str(end_time)+'"}')
				if result == True:
					print ("'last_recent_retrieved_time' updated.")
				else:
					print (result)
				
				##################
				## create model ##
				##################
				machine_learning_api = ml_api+"?task=build_model&config_url="+uploaded_dataset_config_url+"&callback_api="+current_api
				
				r = requests.get(machine_learning_api)
				if r.status_code == 200:
					########################
					## ML MODE is Created ##
					########################
					#Creating the models will take several times and mostly it will get timeout error
					#then we don't wait for it's result and we will CallBack current FunctionApp from the ML-API
					print("## Machine Learning Response ##")
					print(r.text)
			elif task == 'save_models_result':
				selected_model = event['queryStringParameters']['selected_model']
				model_id = event['queryStringParameters']['model_id']
				model_params = event['queryStringParameters']['model_params']
				
				ml_model_config = '{"selected_model": "'+selected_model+'", "model_id": "'+model_id+'", "params":'+model_params+'}'
				
				#################################
				## Start Uploading Config File ##
				#################################
				s3 = boto3.client('s3')
				
				temp_dataset = '/tmp/ML_model.json'
				temp_file = open(temp_dataset,'w+').write(ml_model_config)
				#Upload file into S3
				s3.upload_file(temp_dataset, bucket, ML_model_config_file_name)
				#remove ML_model.json
				os.remove(temp_dataset)
				print("{} file uploaded successfully into the {}/{}".format(ML_model_config_file_name, bucket, ML_model_config_file_name))
				#return respond(200, {"message": "{} file uploaded successfully into the {}/{}".format(ML_model_config_file_name, bucket, ML_model_config_file_name)})
				
				############################################
				## request to build model again (retrain) ##
				############################################
				r = requests.get(current_api+"?task=build_model")
				if r.status_code == 200:
					return respond(200, {"message": "retrain started again."})
				else:
					return respond(200, {"message": "'retrain' request has been failed. response code: "+str(r.status_code)})
			elif task == 'add_resource':
				r = requests.get(add_remove_resources_api+"?task=add_new_resource&host_ip="+host_ip+"&callback_api="+current_api)
				if r.status_code == 200:
					########################################
					## Add Resource Request has been sent ##
					########################################
					#It is not meaning that the resource is created!
					#it is just meaning that we sent our "add resource" request successfully
					#and our request has been accepted.
					#because adding resource is time-consuming, we should wait for it
					#it's response will send to 'resource_is_added' case
					return respond(200, {"message": "'Add resource' request has been sent. you need to wait for it's response."})
					'''
					#new resource is created and we need to update database resource list
					result = db('get','{"field_name": "resource_list"}')
				
					if result == False:
						return respond (200, '{"error":"Resource load failed."}')
					else:
						resource_list = json.loads(result)
						
						#add new resource to the list
						now = datetime.datetime.now()
						temp_index = "{}-{}-{}-{}-{}-{}".format(now.year, now.month, now.day, now.hour, now.minute, now.second)
						resource_list[temp_index] = r.text
						
						result = db('insert','{"field_name": "resource_list", "field_value": "'+json.dumps(resource_list)+'"}')
						
						if result == True:
							return respond(200, {"message": "New resource added to the resource list"})
						else:
							return respond(200, result)
					'''
				else:
					return respond(200, {"message": "'Add resource' request has been failed. response code: "+str(r.status_code)})
			elif task == 'resource_is_added':
				try:
					ip = event['queryStringParameters']['ip']
				except:
					#new resource 'ip' is not passed by GET or POST
					ip = 'no_ip'
					#pass
				
				if ip == 'no_ip':
					print("We could not get the IP for recently added resource. it's the response '{}'".format(event['queryStringParameters']))
					return respond(200, {"message": "We could not get the IP for ewly added resource. it's the response '{}'".format(event['queryStringParameters'])})
				else:
					result = db('get','{"field_name": "resource_list"}')
						
					if result == False:
						#return respond (200, {"error":"Load 'Resource list' from DynamoDB has been failed."})
						#seems it's first added resource. we need to insert it into the DB
						resource_list = []
						
						#add new resource to the list
						resource_list.append(ip)
						resource_list = "::NEW_RESOURCE::".join(str(x) for x in resource_list)
						print (resource_list)
						
						result = db('insert','{"field_name": "resource_list", "field_value": "'+resource_list+'"}')
						
						if result == True:
							return respond(200, {"message": "New resource added to the resource list"})
						else:
							return respond(200, result)
					else:
						#We will update the DB
						resource_list = result.split("::NEW_RESOURCE::")
						
						if ip not in resource_list:
							#add new resource to the list
							resource_list.append(ip)
						
						resource_list = "::NEW_RESOURCE::".join(str(x) for x in resource_list)
						
						result = db('insert','{"field_name": "resource_list", "field_value": "'+resource_list+'"}')
						
						if result == True:
							return respond(200, {"message": "New resource added to the resource list"})
						else:
							return respond(200, result)
			elif task == 'remove_resource':
				result = db('get','{"field_name": "resource_list"}')
						
				if result == False:
					return respond (200, {"error":"Load 'Resource list' from DynamoDB has been failed."})
				else:
					#We need to POP last resource and then send it as a request
					resource_list = result.split("::NEW_RESOURCE::")
					
					#Get last added resource from the list
					if len(resource_list) == 0:
						#there is no more resource
						return respond(200, {"message": "There is no more resource to remove."})
					else:
						latest_added_resource = resource_list.pop()
						
						r = requests.get(add_remove_resources_api+"?task=remove_resource&resource_ip="+latest_added_resource+"&host_ip="+host_ip+"&callback_api="+current_api)
						if r.status_code == 200:
							###########################################
							## Remove Resource Request has been sent ##
							###########################################
							#It is not meaning that the resource is removed!
							#it is just meaning that we sent our "remove resource" request successfully
							#and our request has been accepted.
							#because removing resource is time-consuming, we should wait for it
							#it's response will send to 'resource_is_removed' case
							return respond(200, {"message": "'Remove resource' request has been sent. you need to wait for it's response."})
							'''
							#last resource is removed and we need to update database resource list
							result = db('get','{"field_name": "resource_list"}')
						
							if result == False:
								return respond (200, '{"error":"Resource load failed."}')
							else:
								resource_list = json.loads(result)
								
								#update resources list
								removed_resource_index = json.loads(r.text)['resource_id']
								resource_list.pop('key', None)
								
								result = db('insert','{"field_name": "resource_list", "field_value": "'+json.dumps(resource_list)+'"}')
								
								if result == True:
									return respond(200, {"message": "Last resource removed from the resource list"})
								else:
									return respond(200, result)
							'''
						else:
							return respond(200, {"message": "'Remove resource' request has been failed. response code: "+str(r.status_code)})
			elif task == 'resource_is_removed':
				try:
					ip = event['queryStringParameters']['ip']
				except:
					#new resource 'ip' is not passed by GET or POST
					ip = 'no_ip'
					#pass
				
				if ip == 'no_ip':
					print("We could not get the IP for recently removed resource. it's the response '{}'".format(event['queryStringParameters']))
					return respond(200, {"message": "We could not get the IP for ewly added resource. it's the response '{}'".format(event['queryStringParameters'])})
				else:
					result = db('get','{"field_name": "resource_list"}')
						
					if result == False:
						#seems there is no resource list into the database
						return respond (200, {"error":"Load 'Resource list' from DynamoDB has been failed."})
					else:
						#We will update the DB
						resource_list = result.split("::NEW_RESOURCE::")
						
						#Remove recently removed resource from the list
						temp_resource_list = []
						for resrc in resource_list:
							if resrc != ip:
								temp_resource_list.append(resrc)
							
						temp_resource_list = "::NEW_RESOURCE::".join(str(x) for x in temp_resource_list)
						if temp_resource_list == '':
							result = db('delete','{"field_name": "resource_list"}')
						else:
							result = db('insert','{"field_name": "resource_list", "field_value": "'+temp_resource_list+'"}')
						
						if result == True:
							return respond(200, {"message": "resource {} removed from the resource list".format(ip)})
						else:
							return respond(200, result)
			elif task == 'predict':
				###################
				## Configuration ##
				###################
				for_last_n_minutes = 10
				try:
					for_last_n_minutes = int(event['queryStringParameters']['for_last_n_minutes'])
				except:
					#for_last_n_minutes is not passed by GET or POST
					print ('using default "{}" minutes for_last_n_minutes'.format(for_last_n_minutes))
				
				############################
				## SET START AND END TIME ##
				############################
				#we need to set time period in "timestamp" format
				date = time.time()
				#set "end_time" to one minute ago to make sure that metrics are collected
				#then "end_time" is current time minus one minute
				end_time = math.floor(date) - 60
				#we want to collect metrics for 10 minutes.
				#then "start_time" will be end_time - 10minutes
				start_time = end_time - (for_last_n_minutes * 60)
				
				########################
				## Load ML_model.json ##
				########################
				s3 = boto3.client('s3')
				
				ML_model_config_file_exists = False
				
				s3_resource = boto3.resource('s3')
				s3_bucket = s3_resource.Bucket(bucket)
				object_summary_iterator = s3_bucket.objects.all()
				for my_object in object_summary_iterator:
					if my_object.key == ML_model_config_file_name:
						ML_model_config_file_exists = True
				
				if ML_model_config_file_exists:
					temp_ML_model_config = s3.get_object(Bucket=bucket, Key=ML_model_config_file_name)
					print("Sucessfully downloaded blob {}.".format(ML_model_config_file_name))
					
					if int(temp_ML_model_config['ResponseMetadata']['HTTPStatusCode']) == 200:
						ML_model_config_in_string = temp_ML_model_config['Body'].read().decode('utf-8')
					if len(ML_model_config_in_string) > 0:
						ML_model_config = json.loads(ML_model_config_in_string)
						collected_metrics = get_metrics (start_time, end_time, grafana_API)
						print('metrics are collected for {} minute(s)'.format(end_time - start_time))
						
						normilized_dataset = normilize (collected_metrics)
						print ('dataset is normilized now')
						
						predict_data_array = []
						predict_data_query_string = ""
						for key in normilized_dataset:
							temp_query_str = str(normilized_dataset[key]['cpu'])+","+str(normilized_dataset[key]['memory'])+","+str(normilized_dataset[key]['network_in'])+","+str(normilized_dataset[key]['network_out'])
							predict_data_array.append({"original_metrics": normilized_dataset[key], "query_string": temp_query_str})
							if predict_data_query_string == "":
								predict_data_query_string += "predict_data[]="+temp_query_str
							else:
								predict_data_query_string += "&predict_data[]="+temp_query_str
								
						predict_url = ml_api+"?task=predict&model_id="+ML_model_config['model_id']+"&"+predict_data_query_string
						
						print('Start predicting')
						
						r = requests.get(predict_url)
						if r.status_code == 200:
							prediction_result = json.loads(r.content)
							for idx, val in enumerate(prediction_result):
								predict_data_array[idx]["original_metrics"]["predicted_as"] = val
							
							###############################
							## ALL METRICS ARE PREDICTED ##
							###############################
							print("Start configuring for future prediction")
							
							###################################################
							## Load Original DataSet (saved on blob storage) ##
							###################################################
							print("Start loading '{}'.".format(dataset_blobName))
							dataset_blob_file_exists = False
							#s3_resource = boto3.resource('s3')
							#s3_bucket = s3_resource.Bucket(bucket)
							#object_summary_iterator = s3_bucket.objects.all()
							for my_object in object_summary_iterator:
								if my_object.key == dataset_blobName:
									dataset_blob_file_exists = True
							
							if dataset_blob_file_exists:
								temp_dataset_file = s3.get_object(Bucket=bucket, Key=dataset_blobName)
								
								if int(temp_dataset_file['ResponseMetadata']['HTTPStatusCode']) == 200:
									print("'{}' sucessfully downloaded.".format(dataset_blobName))
									dataset_file_in_string = temp_dataset_file['Body'].read().decode('utf-8')
								
								if len(dataset_file_in_string) > 0:
									############################
									## Declare main variables ##
									############################
									csv_rows = []
									index = 0
									
									future_predicted = [];
									
									##################################################
									## Convert Original Dataset to a sortable array ##
									##################################################
									reader = csv.DictReader(io.StringIO(dataset_file_in_string))
									title = reader.fieldnames
									for row in reader:
										#row include:
										#[('date', '2018-07-31'), ('time', '15:34'), ('cpu', '14.240624999996115'), ('memory', '66.91292607681947'), ('network_in', '6241.410300038755'), ('network_out', '6447.728210074827'), ('final_target', '47.74071773909001'), ('final_class', '2')]
										#{'Final_Target': '10.31290488', 'NetworkOut_Average': '24534', 'NetworkIn_Average': '20633', 'CPUUtilization_Average': '17', 'MemoryUtilization_Average': '5.477561981'}
										
										##################################################
										## Convert Original Dataset to a sortable array ##
										##################################################
										row['index'] = index
											
										csv_rows.append({'index': index, "distance": "unknown", 'statistics_holder': row})
										
										index += 1
										
									############################
									## Load Predicted results ##
									############################
									#prediction_result = [38.2909240722656, 43.9702110290527, 37.5441398620605, 44.5855293273925, 37.1401634216308, 39.3730659484863, 42.2084693908691, 60.3783950805664, 55.1704139709472, 41.3145446777343]
									
									#predicted_record => PR
									#PR = {'CPUUtilization_Average': '1.0', 'NetworkIn_Average': '0.0', 'NetworkOut_Average': '0.0', 'MemoryUtilization_Average': '33.0230580446611', 'time': '2018-03-03 16:52:00+00:00', 'predicted_as': 18.686485290527344}
									for PR in prediction_result:
										for row in csv_rows:
											######################################################
											## Calculate Distance for recently predicted record ##
											######################################################
											# a sample of predicted record is like this:
											#{'CPUUtilization_Average': '1.0', 'NetworkIn_Average': '0.0', 'NetworkOut_Average': '0.0', 'MemoryUtilization_Average': '33.0230580446611', 'time': '2018-03-03 16:52:00+00:00', 'predicted_as': 18.686485290527344}
											
											#csv_rows[0] is something like:
											#{'index': 0, 'weight': 'unknown', 'statistics_holder': {'index': 0, 'CPUUtilization_Average': '17', 'MemoryUtilization_Average': '5.477561981', 'NetworkIn_Average': '20633', 'Final_Target': '10.31290488', 'NetworkOut_Average': '24534'}}
											
											pr_tar = float(PR)
											r_tar = float(row['statistics_holder']["final_target"])
											
											distance = math.sqrt( math.pow(pr_tar - r_tar, 2) )
											
											csv_rows[row['index']]['distance'] = distance
										
										############################
										## Calculate max distance ##
										############################
										percent_of_calculation = 0.25 #25%
									
										#sort by distance
										sorted_rows_by_distance = sorted(csv_rows, key=lambda x : x['distance'], reverse=False)
										
										#calculate maximum defference minimum and maximum distance
										deff = sorted_rows_by_distance[len(sorted_rows_by_distance) - 1]["distance"] - sorted_rows_by_distance[0]["distance"]
										max_dist = deff * percent_of_calculation
										
										#####################
										## Index Neighbors ##
										#####################
										index_of_neighbors = []
										for row in csv_rows:
											if csv_rows[row['index']]['distance'] < max_dist:
												#this record is neighbor
												index_of_neighbors.append(row['index'])
										
										##########################################################
										## Calculate average for each Neighbors in future_steps ##
										##########################################################
										# I want to know what is the average of distance for each neighbor in future
										# and I have future_steps as a limit to calculate for future.
										future_steps = 10
										neighbor_averages = []
										
										for neighbor in index_of_neighbors:
											#then, here, 'neighbor' is index of the row in original dataset
											average = 0
											nei = csv_rows[neighbor]['statistics_holder'] #neighbor point => nei
											#csv_rows[0] is something like:
											#{'index': 0, 'weight': 'unknown', 'statistics_holder': {'index': 0, 'CPUUtilization_Average': '17', 'MemoryUtilization_Average': '5.477561981', 'NetworkIn_Average': '20633', 'Final_Target': '10.31290488', 'NetworkOut_Average': '24534'}}
											
											try:
												nei_tar = float(nei["final_target"])
												r_tar = float(csv_rows[neighbor + 10]['statistics_holder']["final_target"])
												
												#distance = math.sqrt( math.pow(nei_cpu - r_cpu, 2) + math.pow(nei_mem - r_mem, 2) + math.pow(nei_ni - r_ni, 2) + math.pow(nei_no - r_no, 2) + math.pow(nei_tar - r_tar, 2) )
												distance = r_tar - nei_tar
												#print ("distance of P" + str(neighbor + 10) + " => " + str(distance))
												#average += distance
												neighbor_averages.append(distance)
											except:
												#print ("Current point is '{}'	Next retrieved point is '{}'	Number of all points '{}'".format(neighbor, neighbor + next_index, len(csv_rows)))
												pass
												
											#average = average / future_steps
											
										
										#######################################
										## Calculate average of all averages ##
										#######################################
										final_average = 0
										for ave in neighbor_averages:
											final_average += ave
										
										if len(neighbor_averages) == 0:
											#print ("System can't predict future for next {} minute(s) of {}% of data in {} record".format(future_steps, percent_of_calculation, len(csv_rows)))
											print ("There is not enough neighbor for predicted value '{}' to do future prediction. Dataset is not large or it's data is not distributed good enough".format(PR))
										else:
											final_average = final_average / len(neighbor_averages)
											temp_future_predicted = float(PR) + final_average
											future_predicted.append(temp_future_predicted)
											print (temp_future_predicted)
									
									if len(future_predicted) > 0:
										######################################################
										## make desition based on Future Prediction results ##
										######################################################
										temp_future_precition_average = 0
										for fp in future_predicted:
											temp_future_precition_average += fp
										
										temp_future_precition_average = temp_future_precition_average / len(future_predicted)
										print ("System status is in {}%.".format(temp_future_precition_average))
										'''
										#print (current_api+"?task=add_resource")
										#exit()
										if temp_future_precition_average < 40:
											#####################
											## remove resource ##
											#####################
											r = requests.get(current_api+"?task=remove_resource")
											if r.status_code == 200:
												return respond(200, {"message": "Send request to reduce the resources."})
											else:
												return respond(200, {"message": "'Reduce resource' request has been failed. response code: "+str(r.status_code)})
										elif 70 < temp_future_precition_average:
											##################
											## Add Resource ##
											##################
											r = requests.get(current_api+"?task=add_resource")
											if r.status_code == 200:
												return respond(200, {"message": "Send request to increase the resources."})
											else:
												return respond(200, {"message": "'Increase resource' request has been failed. response code: "+str(r.status_code)})
										'''
									
							else:
								print("{} file is not exist into the {}. you need to run 'build_model' first. it will create Dataset automatically.".format(dataset_blobName, bucket))
						else:
							print("Prediction is not working. check ML_API ({})".format(predict_url))
							exit()
						
				else:
					print("{} is not exist! you need to build model first.".format(ML_model_config_file_name))
			elif task == 'ndbench_auto_limit':
				try:
					status = event['queryStringParameters']['status']
				except:
					#'status' is not passed by GET or POST
					status = 'no_status'
					#pass
				
				if status == 'stop':
					#it is a request to 'stop'.
					#then we will set the status to 'stop'
					result = db('insert','{"field_name": "ndbench_auto_limit", "field_value": "stop"}')
					print("'ndbench_auto_limit' is set to 'stop'.")
					#return respond(200, {"message": "'ndbench_auto_limit' is set to 'stop'."})
				elif status == 'start':
					#it is a request to 'start'
					result = db('insert','{"field_name": "ndbench_auto_limit", "field_value": "start"}')
					print("'ndbench_auto_limit' is set to 'start'.")
					#return respond(200, {"message": "'ndbench_auto_limit' is set to 'start'."})
				
				#GET the status and act related to that
				result = db('get','{"field_name": "ndbench_auto_limit"}')
				
				if result == False:
					#seems something is wrong with Database, maybe 'ndbench_auto_limit' is not set yet into the database!
					return respond (200, {"error":"Load 'ndbench_auto_limit' from DynamoDB has been failed."})
				elif result == 'start':
					#Act related to status
					select_limit = random.randrange(0, 3)
					
					readRateLimit = 1
					writeRateLimit = 1
					
					limits = ["Low", "Normal", "High"]
					
					new_limit = limits[select_limit]
					
					if new_limit == "Low":
						readRateLimit = random.randrange(1, 2000)
						writeRateLimit = random.randrange(1, 2000)
					elif new_limit == "Normal":
						readRateLimit = random.randrange(2000, 9000)
						writeRateLimit = random.randrange(2000, 9000)
					elif new_limit == "High":
						readRateLimit = random.randrange(9000, 12001)
						writeRateLimit = random.randrange(9000, 12001)
					
					conf_json = {"readRateLimit": readRateLimit, "writeRateLimit": writeRateLimit}
					
					r = requests.post(NdbenchAPI+"REST/ndbench/config/set", json=conf_json)
					if r.status_code == 200:
						print ("New limit is '{}': {}".format(new_limit, json.dumps(conf_json)))
						return respond (200, {"message":"New limit is '{}': {}".format(new_limit, json.dumps(conf_json))})
					else:
						print ("NdbenchAPI is not available.")
						return respond (200, {"error":"NdbenchAPI is not available. status_code is: {}".format(r.status_code)})
				
				
def get_metrics (start_time, end_time, grafana_API):
	memory_query = grafana_API + 'avg ((node_memory_MemTotal_bytes-node_memory_MemFree_bytes-node_memory_Cached_bytes)/(node_memory_MemTotal_bytes)*100)&start='+str(start_time)+'&end='+str(end_time)+'&step=60'
	cpu_query = grafana_API + 'avg(100-(avg by(instance)(irate(node_cpu_seconds_total{mode="idle"}[5m]))*100))&start='+str(start_time)+'&end='+str(end_time)+'&step=60'
	network_in = grafana_API + 'avg(node_network_receive_bytes_total)&start='+str(start_time - 60)+'&end='+str(end_time)+'&step=60'
	network_out = grafana_API + 'avg(node_network_transmit_bytes_total)&start='+str(start_time - 60)+'&end='+str(end_time)+'&step=60'
	
	collected_metrics = {}
	
	r = requests.get(memory_query)
	collected_metrics["memory"] = json.loads(r.content)['data']['result'][0]['values']
	print ('## MEMORY data has been received ##')
	
	r = requests.get(cpu_query)
	collected_metrics["cpu"] = json.loads(r.content)['data']['result'][0]['values']
	print ('## CPU data has been received ##')
	
	r = requests.get(network_in)
	collected_metrics["network_in"] = json.loads(r.content)['data']['result'][0]['values']
	print ('## NETWORK IN data has been received ##')
	
	r = requests.get(network_out)
	collected_metrics["network_out"] = json.loads(r.content)['data']['result'][0]['values']
	print ('## NETWOKR OUT data has been received ##')
	
	return collected_metrics

def normilize (collected_metrics):
	temp_output = {}
	final_output = {}
	
	for index, value in enumerate(collected_metrics["memory"]):
		unix_timestamp  = int(value[0])
		local_time = time.localtime(unix_timestamp)
		#print(time.strftime("%Y-%m-%d %H:%M:%S", local_time))
		temp_date = time.strftime("%Y-%m-%d", local_time)
		temp_time = time.strftime("%H:%M", local_time)
		
		query_time = time.strftime("%Y_%m_%d_%H_%M", local_time)
		try:
			temp_output[query_time]
		except:
			temp_output[query_time] = {}
			final_output[query_time] = {}
			
		##################################################
		## Network is Aggregated then we should solve this problem
		## Maximum Network capability is 500Mbps = 62.5MBps
		## read more about capabilities:
		## https://www.vioreliftode.com/index.php/what-does-microsoft-mean-by-low-moderate-high-very-high-extremely-high-azure-network-bandwidth-part-1/
		##################################################
		collected_metrics["network_in"][index+1][1]
		collected_metrics["network_in"][index][1]
		collected_metrics["network_out"][index+1][1]
		collected_metrics["network_out"][index][1]
		collected_metrics["cpu"][index][1]
		collected_metrics["memory"][index][1]
		
		try:
			network_in = math.fabs( ( float(collected_metrics["network_in"][index+1][1]) - float(collected_metrics["network_in"][index][1]) ) / 1024)
			network_out = math.fabs( ( float(collected_metrics["network_out"][index+1][1]) - float(collected_metrics["network_out"][index][1]) ) / 1024)
			
			temp_output[query_time]["date"] = temp_date
			temp_output[query_time]["time"] = temp_time
			temp_output[query_time]["original_network_in"] = network_in#;//parseFloat(collected_metrics.network_in[index][1]);
			temp_output[query_time]["original_network_out"] = network_out#;//parseFloat(collected_metrics.network_out[index][1]);
			temp_output[query_time]["network_in"] = (network_in * 100) / 640000
			temp_output[query_time]["network_out"] = (network_out * 100) / 640000
			temp_output[query_time]["cpu"] = float(collected_metrics["cpu"][index][1])
			temp_output[query_time]["memory"] = float(value[1])
			
			final_output[query_time]["date"] = temp_date
			final_output[query_time]["time"] = temp_time
			final_output[query_time]["network_in"] = network_in
			final_output[query_time]["network_out"] = network_out
			final_output[query_time]["cpu"] = temp_output[query_time]["cpu"]
			final_output[query_time]["memory"] = temp_output[query_time]["memory"]
		except:
			print("is not possible to normilize index {} of colected metrics".format(index))
			
	###################################
	## Calculate Sum for each metric ##
	###################################
	cpu_total_sum = 0
	memory_total_sum = 0
	network_in_total_sum = 0
	network_out_total_sum = 0
	
	for key in temp_output:
		cpu_total_sum += temp_output[key]["cpu"]
		memory_total_sum += temp_output[key]["memory"]
		network_in_total_sum += temp_output[key]["network_in"]
		network_out_total_sum += temp_output[key]["network_out"]
		
	total_sum = cpu_total_sum + memory_total_sum + network_in_total_sum + network_out_total_sum
	
	normilized_json = {}
	cpu_sum_of_LNs = 0
	memory_sum_of_LNs = 0
	network_in_sum_of_LNs = 0
	network_out_sum_of_LNs = 0
	
	for key in temp_output:
		try:
			normilized_json[key]
		except:
			normilized_json[key] = {}
			
		temp = (temp_output[key]["cpu"]/100)/total_sum
		if temp == 0:
			temp = 0.0000001
			
		temp = temp * math.log(temp)
		normilized_json[key]["cpu"] = temp
		cpu_sum_of_LNs += temp
		
		temp = (temp_output[key]["memory"]/100)/total_sum
		if temp == 0:
			temp = 0.0000001

		temp = temp * math.log(temp)
		normilized_json[key]["memory"] = temp
		memory_sum_of_LNs += temp
		
		temp = (temp_output[key]['network_in']/100)/total_sum
		if temp == 0:
			temp = 0.0000001

		temp = temp * math.log(temp)
		normilized_json[key]['network_in'] = temp
		network_in_sum_of_LNs += temp
		
		temp = (temp_output[key]['network_out']/100)/total_sum
		if temp == 0:
			temp = 0.0000001

		temp = temp * math.log(temp)
		normilized_json[key]['network_out'] = temp
		network_out_sum_of_LNs += temp
		
	weights = {}
	k = 1 / math.log(len(normilized_json))
	cpu_entropy = cpu_sum_of_LNs * (-1 * k)
	memory_entropy = memory_sum_of_LNs * (-1 * k)
	network_in_entropy = network_in_sum_of_LNs * (-1 * k)
	network_out_entropy = network_out_sum_of_LNs * (-1 * k)
	
	sum_of_entropies = cpu_entropy + memory_entropy + network_in_entropy + network_out_entropy
		
	weights['cpu'] = cpu_entropy / sum_of_entropies
	weights['memory'] = memory_entropy / sum_of_entropies
	weights['network_in'] = network_in_entropy / sum_of_entropies
	weights['network_out'] = network_out_entropy / sum_of_entropies
	
	for key in temp_output:
		temp_final_target = temp_output[key]['cpu'] * weights['cpu'] + temp_output[key]['memory'] * weights['memory'] +  temp_output[key]['network_in'] * weights['network_in'] + temp_output[key]['network_out'] * weights['network_out']
	
		final_target_class = 1 #Low
		if 45 < temp_final_target and temp_final_target <= 60:
			final_target_class = 2 #Normal
		elif 60 < temp_final_target:
			final_target_class = 3 #High
	
		temp_output[key]['final_target'] = temp_final_target
		temp_output[key]['final_class'] = final_target_class
	
		final_output[key]['final_target'] = temp_final_target
		final_output[key]['final_class'] = final_target_class
	
	return final_output
	
def upload_dataset (normilized_dataset, bucket, dataset_blobName='dataset.csv', dataset_config_blobName='dataset_config.json'):
	########################
	## Load ML_model.json ##
	########################
	s3 = boto3.client('s3')
	dataset_string = 'date,time,cpu,memory,network_in,network_out,final_target,final_class\r\n'
	
	#####################################
	## Load Currently Uploaded Dataset ##
	#####################################
	dataset_is_exist = False
	
	s3_resource = boto3.resource('s3')
	s3_bucket = s3_resource.Bucket(bucket)
	object_summary_iterator = s3_bucket.objects.all()
	for my_object in object_summary_iterator:
		if my_object.key == dataset_blobName:
			dataset_is_exist = True
	
	if dataset_is_exist:
		#on time of writing this code, S3 is not supporting append to the objects.
		#then we can't add collected metrics to the dataset.csv that is saved currently.
		#to do that, we will download the dataset and will append collected metrics to the end of it.
		temp_dataset = s3.get_object(Bucket=bucket, Key=dataset_blobName)
		print("Sucessfully downloaded blob {}.".format(dataset_blobName))
		
		if int(temp_dataset['ResponseMetadata']['HTTPStatusCode']) == 200:
			old_dataset = temp_dataset['Body'].read().decode('utf-8')
		if len(old_dataset) > 0:
			dataset_string = old_dataset
	
	for key in normilized_dataset:
		dataset_string += str(normilized_dataset[key]['date']) +","+ str(normilized_dataset[key]['time']) +","+ str(normilized_dataset[key]['cpu']) +","+ str(normilized_dataset[key]['memory']) +","+ str(normilized_dataset[key]['network_in']) +","+ str(normilized_dataset[key]['network_out']) +","+ str(normilized_dataset[key]['final_target']) +","+ str(normilized_dataset[key]['final_class']) +"\r\n"
		
	#####################
	## Start Uploading ##
	#####################
	s3 = boto3.client('s3')
	
	'''dataset_blob_exists = False
	
	s3_resource = boto3.resource('s3')
	s3_bucket = s3_resource.Bucket(bucket)
	object_summary_iterator = s3_bucket.objects.all()
	for my_object in object_summary_iterator:
		if my_object.key == dataset_blobName:
			dataset_blob_exists = True
	'''
	temp_dataset = '/tmp/temp_dataset.csv'
	temp_file = open(temp_dataset,'w+').write(dataset_string)
	#Upload file into S3
	s3.upload_file(temp_dataset, bucket, dataset_blobName)
	#remove temp_dataset.csv
	os.remove(temp_dataset)
	print('{} file uploaded successfully into the {}/{}'.format(dataset_blobName, bucket, dataset_blobName))
	
	#################################
	## Start Uploading Config File ##
	#################################
	dataset_config = '{"type": "csv", "name": "'+dataset_blobName+'", "url":"https://s3.amazonaws.com/'+bucket+'/'+dataset_blobName+'", "has_header_row": "yes", "train_columns": [{"col_name": "cpu", "col_number": "2"}, {"col_name": "memory", "col_number": "3"}, {"col_name": "network_in", "col_number": "4"}, {"col_name": "network_out", "col_number": "5"}], "multiclass_target_col": {"col_name": "final_class", "col_number": "7"}, "regression_target_col": {"col_name": "final_target", "col_number": "6"}, "export_model_name": "ski_model"}'
	
	temp_dataset_config_file = '/tmp/temp_dataset_config_file.json'
	temp_file = open(temp_dataset_config_file,'w+').write(dataset_config)
	#Upload file into S3
	s3.upload_file(temp_dataset_config_file, bucket, dataset_config_blobName)
	#remove temp_dataset_config_file.json
	os.remove(temp_dataset_config_file)
	print('{} file uploaded successfully into the {}/{}'.format(dataset_config_blobName, bucket, dataset_config_blobName))
	
	return ('https://s3.amazonaws.com/'+bucket+'/'+dataset_config_blobName)