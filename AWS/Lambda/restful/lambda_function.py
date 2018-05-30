import boto3
import json
import xml.etree.ElementTree as ET #https://docs.python.org/3/library/xml.etree.elementtree.html

#related to this topic we can use "queryStringParameters"
#https://stackoverflow.com/questions/31329958/how-to-pass-a-querystring-or-route-parameter-to-aws-lambda-from-amazon-api-gatew

def respond(err, res=None):
	return {
		'statusCode': '400' if err else '200',
		'body': err.message if err else json.dumps(res),
		'headers': {
			'Content-Type': 'application/json',
		},
	}

ec2 = boto3.resource('ec2')

def lambda_handler(event, context):
	def pars_xml_tag(xml_node, response):
		response += xml_node.tag + ": " + xml_node.text + " \n"
		if xml_node.attrib:
			response += "Attribute for \"" + xml_node.tag + "\": " + json.dumps(xml_node.attrib) + "\n"
		for child in xml_node:
			response = pars_xml_tag(child, response)
		
		return response
		
	s3 = boto3.client('s3')
	s3_resource = boto3.resource('s3')
	operation = event['httpMethod']
	#return respond(None, json.dumps(event))
	
	
	if operation == 'POST' or operation == 'GET':
		bucket_name = 'multiple-targets'#db('get','{"field_name": "bucket"}')
		xml_file_name = 'config.xml'
		xml_path = 'RESTful'
		xml_is_exist = False
		full_path = xml_path+'/'+xml_file_name
		response = ""
		
		try:
			req = event['queryStringParameters']['req']
		except:
			req = 'no-request'
		
		if req == 'no-request':
			return respond(None, {"error": "there is no \"req\" parameter in your request..! Send your request using json format via POST method: {\"req\"=\"YOUR-REQUEST-NAME\"}"})
		else:
			#Is XML Config file exsit or not?
			paginator = s3.get_paginator('list_objects')
			operation_parameters = {'Bucket': bucket_name, 'Prefix': xml_path}
			page_iterator = paginator.paginate(**operation_parameters)
			
			for page in page_iterator:
				try:
					for obj in page['Contents']:
						#print (obj['Key'])
						if obj['Key'] == full_path:
							xml_is_exist = True
							break
				except:
					print("Config directory ({}) is not exist".format(bucket_name+"/"+xml_path))
					s3.put_object(Bucket=bucket_name, Key=(xml_path+'/'))
					
			if not xml_is_exist:
				#XML file isn't exist
				#print(full_path + " is not exist..!")
				return respond(None, full_path + " is not exist..!")
			else:
				old_file_object = s3.get_object(Bucket=bucket_name, Key=full_path)
				if int(old_file_object['ResponseMetadata']['HTTPStatusCode']) == 200:
					xml_content = old_file_object['Body'].read().decode('utf-8')
					#print (xml_content)
					#ET.parse() #parse from file
					#ET.fromstring() #parse from string
					root = ET.fromstring(xml_content)
					#response = "Hi, I am coming from "+ xml_file_name + ":\n"
					
			#XML is exist, it's time to handel the request
			if req == 'system_dataset_info':
				node_path = "system_dataset_file/"
				type = root.find(node_path+'type').text
				name = root.find(node_path+'name').text
				has_header_row = root.find(node_path+'has_header_row').text
				train_columns = []
				temp_node = root.find(node_path+'columns_should_train')
				for child in temp_node:
					train_columns.append({'col_name':child.text, 'col_number': child.attrib["col_number"]})
				
				temp_node = root.find(node_path+'multiclass_target_col')
				multiclass_target_col = {'col_name':temp_node.text, 'col_number': temp_node.attrib["col_number"]}
				
				temp_node = root.find(node_path+'regression_target_col')
				regression_target_col = {'col_name':temp_node.text, 'col_number': temp_node.attrib["col_number"]}
				
				export_model_name = root.find(node_path+'export_model_name').text
				return respond(None, {'type':type, 'name':name, 'has_header_row':has_header_row, 'train_columns':train_columns, 'multiclass_target_col':multiclass_target_col, 'regression_target_col':regression_target_col, 'export_model_name':export_model_name})
				
			if req == 'system_export_model_name':
				node_path = "system_dataset_file/"
				export_model_name = root.find(node_path+'export_model_name').text
				return respond(None, {'export_model_name':export_model_name})
				
			if req == 'all':
				response = pars_xml_tag(root, response)
				
			return respond(None, response)