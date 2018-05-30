import boto3
from datetime import datetime
from datetime import timedelta
import time
import json
import os
import csv

def db (do, data):
	dynamodb_table_name = 'automation2'
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(dynamodb_table_name)
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
		
	if do == 'delete':
		#update data['value'] for data['name'] into the database
		table.delete_item(
			Key={
				'field_name': data['field_name'],
				'hack': 'dynamodb'
			}
		)
		
arns = db('get','{"field_name": "arns"}')

def publish_to_sns(message, arn, delay):
	time.sleep(delay) #sleep for "delay" second
	if arn == '':
		#use default arn (Controler SNS)
		arn = str(arns[0]["CloudWatch"])
		
	sns = boto3.client('sns')
	return sns.publish(
		TopicArn=arn,
		Message=json.dumps(message),
		MessageStructure='string',
		MessageAttributes={
		   'summary': {
				  'StringValue': 'just a summary',
				  'DataType': 'String'
		   }
		}
	)
	
#define the connection
ec2 = boto3.resource('ec2')
cw = boto3.client('cloudwatch')

def lambda_handler(event, context):
	#we compared Multiclass & Regression results after Cross Validation
	compare_result = db('get','{"field_name": "compare_result"}')
	if compare_result == False:
		#we don't have compare result, then we can't predict anything!
		print ('Ops! Somebody deleted Dynamodb! or nobody started Lambda_Controler yet')
		return False
		#raise
	elif compare_result == 'Regression':
		#we should use Regression model
		pridiction_ml_model_id = db('get','{"field_name": "regression_model_id"}')
	else:
		#we should use Multiclass model
		pridiction_ml_model_id = db('get','{"field_name": "multiclass_model_id"}')
		
	#we should count how many times we use prediction before. because we want to get result of prediction
	#each X preiod of usage
	how_many_realtime_prediction = int(db('get','{"field_name": "how_many_realtime_prediction"}'))
	how_many_realtime_prediction = how_many_realtime_prediction + 1
	db('insert','{"field_name": "how_many_realtime_prediction", "field_value": '+str(how_many_realtime_prediction)+'}')
		
	#####################################################################requested_instance_id = db('get','{"field_name": "instance_id"}')
	requested_instance_id = "i-05a2d1f80d0360668"
	# Use the filter() method of the instances collection to retrieve
	# all running EC2 instances.
	filters = [{
			'Name': 'instance-state-name', 
			'Values': ['running']
		}
	]
	
	#filter the instances
	instances = ec2.instances.filter(Filters=filters)
	
	instance_found = False
	for instance in instances:
		#print(instance.id, instance.instance_type)
		#print (instance.tags)
		inst_id = instance.id
		inst_name = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'][0]
		
		end = datetime.utcnow() - timedelta(minutes=1)
		start = end - timedelta(minutes=10)
		period = 60 #one minute

		if inst_id == requested_instance_id:
			instance_found = True
			print('Requested instance (ID: {}) found'.format(requested_instance_id))
			
			result_types = [
				{
				'name': 'CPUUtilization',
				'stat':['SampleCount','Average','Sum','Minimum','Maximum'],
				'unit': 'Percent'
				},
				{
				'name': 'NetworkIn',
				'stat':['SampleCount','Average','Sum','Minimum','Maximum'],
				'unit': 'Bytes'
				},
				{
				'name': 'NetworkOut',
				'stat':['SampleCount','Average','Sum','Minimum','Maximum'],
				'unit': 'Bytes'
				},
				{
				'name': 'MemoryUtilization',
				'stat':['SampleCount','Average','Sum','Minimum','Maximum'],
				'unit': 'Percent'
				}
			]
			
			config = {"network_in_max": 10737418240, "network_out_max": 10737418240}
			temp = {}
			count = 0;
			timestamps = []
			datapoints_in_json = ""
			
			for type in result_types:
				namespace = 'AWS/EC2'
				if type['name'] == 'MemoryUtilization':
					namespace = 'System/Linux'
					
				temp_results = cw.get_metric_statistics(
					Namespace= namespace,
					MetricName= type['name'],
					Unit= type['unit'],
					Dimensions=[{'Name': 'InstanceId', 'Value': requested_instance_id}],
					StartTime=start,
					EndTime=end,
					Period=period,
					Statistics= type['stat']
				)
				#print (len(temp_results['Datapoints']))
				temp[type['name']] = temp_results['Datapoints']
			
			###################################
			## Set Network Maximum bandwidth ##
			###################################
			for key, metrics in temp.items():
				for row in metrics:
					row['type'] = key
					
					if key == "NetworkIn":
						if row["Average"] > config["network_in_max"]:
							config["network_in_max"] = row["Average"]
					elif key == "NetworkOut":
						if row["Average"] > config["network_out_max"]:
							config["network_out_max"] = row["Average"]
							
					if row['Timestamp'] not in timestamps:
						timestamps.append(row['Timestamp']) #add new timestamp to our timestamps
			
			def jsonDefault(object):
				return str(object)
				
			for key, metrics in temp.items():
				if count > 0:
					datapoints_in_json += ','
					
				datapoints_in_json += json.dumps(metrics, default=jsonDefault)
				
				count += 1
			
			json_result = json.loads('['+datapoints_in_json+']')
			temp_json = {}
			
			for row in json_result:
				############################################
				## Doing a loop on each row of statistics ##
				############################################
				for element in row:
					type = str(element['type']) #something like CPUUtilization, DiskReadBytes and ...
					
					########################################################
					## Normilize Metrics (Convert all metrics to percent) ##
					########################################################
					if type == "NetworkIn":
						element['Average'] = "{0:.2f}".format((element['Average'] * 100) / config["network_in_max"])
					elif type == "NetworkOut":
						element['Average'] = "{0:.2f}".format((element['Average'] * 100) / config["network_out_max"])
					
					#>>>>>>>>>>>>>>>overview = preparation(element, overview)
					#print averages
					target = '1'#Low
					average = float(element['Average'])

					if 45 < average and average <= 60:
						target = '2'#Normal
					elif 60 < average:
						target = '3'#High
						
					timestamp = str(element['Timestamp']) #2017-05-29 20:18:00+00:00
						

					#we should merge duplicated reports (for CPUUtilization, DiskReadBytes and ...) to one row.
					#those reports has same timestamp, then we check to make sure we have timestamp object just one time
					try:
						temp_json[timestamp]
					except KeyError:
						temp_json[timestamp] = {}
						
					temp_json[timestamp]['Date'] = timestamp[0:10]
					temp_json[timestamp]['Time'] = timestamp[11:19]
					temp_json[timestamp][type+'_Average'] = float(element['Average'])
					temp_json[timestamp][type+'_Target'] = target
			
			rebuild_json_to_sort = []
			
			for key in temp_json:
				if temp_json[key]:
					rebuild_json_to_sort.append({'Timestamp': key, 'metrics': temp_json[key]})
				
			sorted_json = sorted(rebuild_json_to_sort, key=lambda x : x['Timestamp'], reverse=False)
			
			for key in sorted_json:
				#key['metrics] include something like this:
				#{'Date': '2018-02-23', 'Time': '23:38:00', 'CPUUtilization_Average': 1.0, 'CPUUtilization_Target': '1', 'NetworkIn_Average': 0.0, 'NetworkIn_Target': '1', 'NetworkOut_Average': 0.0, 'NetworkOut_Target': '1', 'MemoryUtilization_Average': 33.4308880971843, 'MemoryUtilization_Target': '1'}
				record = {}
				record['CPUUtilization_Average'] = str(key['metrics']['CPUUtilization_Average'])
				record['NetworkIn_Average'] = str(key['metrics']['NetworkIn_Average'])
				record['NetworkOut_Average'] = str(key['metrics']['NetworkOut_Average'])
				record['MemoryUtilization_Average'] = str(key['metrics']['MemoryUtilization_Average'])
				
				time.sleep(0.005) #prediction is limited to 200 predict in each second
				prediction_output = realtime_predict(pridiction_ml_model_id, record)
				#print ("time: " + str(key['Timestamp']) + " >> " + prediction_output)
				#{"predictedValue": 18.686485290527344, "details": {"Algorithm": "SGD", "PredictiveModelType": "REGRESSION"}, "latency_ms": 61.87152862548828}
				record['time'] = str(key['Timestamp'])
				prediction_output_json = json.loads(prediction_output)
				if compare_result == 'Regression':
					record['predicted_as'] = prediction_output_json['predictedValue']
				else:
					record['predicted_as'] = prediction_output_json['predictedLabel']
				
				print ("Time => {}, CPU => {}, Predicted As => {}".format(record['time'],record['CPUUtilization_Average'],record['predicted_as']))
			
			return False
			#db('insert','{"field_name": "prediction_result", "field_value": "'+str(prediction_result)+'"}')
			#	print("Result is:\n" + prediction_result)
		

	if instance_found == False:
		print ("Instance (ID:"+requested_instance_id+") doesn't found. check if it's exist or it's running")
			
			
def realtime_predict (ml_model_id, record):
	client = boto3.client('machinelearning')
	model = client.get_ml_model(
		MLModelId=ml_model_id,
		Verbose=True
	)
	#print (record)
	endpoint = model.get('EndpointInfo', {}).get('EndpointUrl', '')
	
	if endpoint:
		#print('ml.predict("%s", %s, "%s") # returns...' % (ml_model_id, json.dumps(record, indent=2), endpoint))
		prediction_str = ''
		
		start = time.time()
		response = client.predict(
			MLModelId=ml_model_id,
			Record=record,
			PredictEndpoint=endpoint
		)
		
		'''
		response is something like this:
		{
			"Prediction": {
			"predictedValue": 0.46085113286972046,
			"details": {
			"Algorithm": "SGD",
			"PredictiveModelType": "REGRESSION"
			}
		}
		'''
		response['Prediction']['latency_ms'] = (time.time() - start)*1000
		
		prediction_str = json.dumps(response['Prediction'])
			
		
		#predictedValue = response['Prediction']['predictedValue']
		#Algorithm = response['Prediction']['details']['Algorithm']
		#PredictiveModelType = response['Prediction']['details']['PredictiveModelType']
		
		#print(json.dumps(response, indent=2))
		#print("Latency: %.2fms" % latency_ms)
		return prediction_str