import boto3
import json
import datetime

def response (code, message):
	return {
		"statusCode": code,
		"headers": {
			"Content-Type": 'text/html',
			"Access-Control-Allow-Origin": "*"
		},
		"body": message
	}
	
def db (do, data):
	dynamodb_table_name = 'hessam'
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
			
		#table.meta.client.get_waiter('table_exists').wait(TableName=dynamodb_table_name)
		#print("DynamoDB is creating. please try again one minute later.")
		#response(200, '{"error":"DynamoDB is creating. please try again one minute later."}')
		return '{"error":"DynamoDB is creating. please try again one minute later."}'
		
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

def is_json(myjson):
	try:
		json_object = json.loads(myjson)
	except:
		return False
	return True
	
def lambda_handler(event, context):
	operation = event['httpMethod']
	
	path = event['path']
	#remoce first and last "/" from the path
	path_first_character = path[0];
	path_last_character = path[len(path) - 1]
	
	if path_last_character == '/':
		path = path[0:len(path) - 1]
	if path_first_character == "/":
		path = path[1:]
	
	segments = path.split("/") 
	
	controller = segments[0].lower()
	
	if controller == 'hello':
		if len(segments) > 1:
			username = segments[1].lower()
			if operation == 'PUT':
				try:
					data = event['body']
				except:
					pass
				
				if data != '' and is_json(data):
					#insert/Update birthday
					userdata = json.loads(data)
					result = db('insert','{"field_name": "'+username+'", "field_value": "'+userdata["dateOfBirth"]+'"}')
					
					if result == True:
						return response(201, '{}')
					else:
						return response(200, result)
				else:
					return response(200, '{"error":"You should send \'data\' in JSON format in your request body. please read the documentation if I had sent any!"}')
			
			elif operation == 'GET':
				result = db('get','{"field_name": "'+username+'"}')
				
				if result == False:
					return response (200, '{"error":"Fail \''+username+'\' is not set"}')
				else:
					date_segments = result.split("-")
					
					if len(date_segments) == 3:
						year = date_segments[0]
						month = int(date_segments[1])
						day = int(date_segments[2])
						
						now = datetime.datetime.now()
						#print now.year, now.month, now.day, now.hour, now.minute, now.second
						
						current_date = datetime.date(now.year,now.month,now.day)
						his_date = datetime.date(now.year,month,day)
						datetime.timedelta(6)
						
						if month < now.month or (month == now.month and day < now.day):
							#his birthday is gone! we need to check for his next birthday
							his_date = datetime.date(now.year+1,month,day)
							
						difference = (his_date-current_date).days
						
						output = "Hello, {}!".format(username)
						
						if difference == 0:
							output = output + ' Happy birthday!'
						else:
							output = output + " your birthday is in {} days".format(difference)
							
						return response(200, json.dumps({"message": output}))
					else:
						return response(200, json.dumps(result))
		else:
			return response (200, '{"error":"You should pass Username in the Query string like this: hello/john"}')
		
	
	else:
		return response (200, '{"error": "Other methods are not supported yet..! call me if you want ;) hessamalipour@gmail.com"}')
