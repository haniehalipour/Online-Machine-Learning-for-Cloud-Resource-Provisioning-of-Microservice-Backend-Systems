from __future__ import print_function

import json
import boto3
import time
from botocore.exceptions import ClientError

print('Main controller Start')
s3 = boto3.client('s3')

#************ Main Config **************
#DynamoDB Table Name
dynamodb_table_name = 'automation2' #dont change it, if you change, you should change all other python files too
#all useful ARN URLs
arns = json.loads("[{\"Controller\": \"arn:aws:sns:us-east-1:********:2conroller\",\"CV_MultiClass\": \"arn:aws:sns:us-east-1:********:2CV_MultiClass\", \"CV_Regression\": \"arn:aws:sns:us-east-1:********:2CV_Regression\", \"MultiClass_model\": \"arn:aws:sns:us-east-1:********:2MultiClassModel\", \"Regression_model\": \"arn:aws:sns:us-east-1:********:2RegressionModel\", \"Manage_resources\": \"arn:aws:sns:us-east-1:********:2ManageResource\" }]")
bucket = 'multiple-targets'

#DATAset directory should include dataset csv file too.
#directory will start from bucket root directory
multiclass_dataset_dir = 'export_to_csv/multiclass_workload.csv'
regression_dataset_dir = 'export_to_csv/regression_workload.csv'
usage_log = 'cpu_usage.txt'
pridiction_log = 'realtime_prediction.txt'
 
#it will use local schema in lambda directory
#make sure you put this schema in the same directory of lambda_function.py
#in this document, everythin with "Root Directory" flag, mean that you should copy your main file in root directory of your function
#************ Cross-Validation Config **************
#Schema name in Cross-Validation and Build model should be same
#becareful their file names for each one in the root directory
multiclass_schema = 'multiclass.csv.schema'#Root Directory
regression_schema = 'regression.csv.schema'#Root Directory
#number of multiclass and regression cross-validation fold
number_of_folds = 4

#************ Get Usage Log (Cloudwatch) Config **************
# set Instance ID to get CloudWatch log form that instance
instance_id = 'i-05a2d1f80d0360668' #powerful-cassandra-1/2

#************ Build Models Config **************
#batch Schema
multiclass_batch_csv_schema = 'multiclass-batch.csv.schema'#Root Directory
regression_batch_csv_schema = 'regression-batch.csv.schema'#Root Directory
#when we are building Models, we can peredict dataset by using created model
#if you want to skip this step, set 'build_model_prediction' to False (it's True by Default)
build_model_prediction = True
#output for prediction after building models
multiclass_ml_output = 'ml-output/'
regression_ml_output = 'ml-output/'
#************ Realtime Prediction **************
#Calculate prediction state after (_) time.
#after it, we will save prediction result state into the database
calculate_prediction_state_after = 10
    
def lambda_handler(event, context):
    global instance_id #I hate Python
    
    dynamodb = boto3.resource('dynamodb')
    db_state = is_database_ready(dynamodb_table_name)
    
    if db_state == 'has_been_exist' or db_state == 'is_created':
        print ("Insert Configuration data into the database")
        table = dynamodb.Table(dynamodb_table_name)
        with table.batch_writer() as batch:
            batch.put_item(
                Item={
                    'field_name': 'arns',
                    'hack': 'dynamodb',
                    'field_value': arns
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'bucket',
                    'hack': 'dynamodb',
                    'field_value': bucket
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'multiclass_dataset_dir',
                    'hack': 'dynamodb',
                    'field_value': multiclass_dataset_dir
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'regression_dataset_dir',
                    'hack': 'dynamodb',
                    'field_value': regression_dataset_dir
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'usage_log',
                    'hack': 'dynamodb',
                    'field_value': usage_log
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'pridiction_log',
                    'hack': 'dynamodb',
                    'field_value': pridiction_log
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'number_of_folds',
                    'hack': 'dynamodb',
                    'field_value': number_of_folds
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'build_model_prediction',
                    'hack': 'dynamodb',
                    'field_value': build_model_prediction
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'multiclass_schema',
                    'hack': 'dynamodb',
                    'field_value': multiclass_schema
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'multiclass_ml_output',
                    'hack': 'dynamodb',
                    'field_value': multiclass_ml_output
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'multiclass_batch_csv_schema',
                    'hack': 'dynamodb',
                    'field_value': multiclass_batch_csv_schema
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'regression_schema',
                    'hack': 'dynamodb',
                    'field_value': regression_schema
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'regression_ml_output',
                    'hack': 'dynamodb',
                    'field_value': regression_ml_output
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'regression_batch_csv_schema',
                    'hack': 'dynamodb',
                    'field_value': regression_batch_csv_schema
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'instance_id',
                    'hack': 'dynamodb',
                    'field_value': instance_id
                }
            )
            batch.put_item(
                Item={
                    'field_name': 'calculate_prediction_state_after',
                    'hack': 'dynamodb',
                    'field_value': calculate_prediction_state_after
                }
            )
            
    else:
        print ("Database is not created..!")
        return False 
    
    message = event['Records'][0]['Sns']['Message']
    json_message = json.loads(str(message))
    
    #remain_millis = context.get_remaining_time_in_millis()
    
    curr_state = str(json_message['state'])
    
    print (":::::::"+curr_state+":::::::::::::::::")
    print (message)
    
    if curr_state == 'error':
        print (json_message['message'])
        #exit from progress by return False..!
        return False
        
    if curr_state == 'log':
        print (json_message['message'])
        #exit from progress by return True..!
        return True
        
    if curr_state == 'create_endpoints':
        #####################################
        # Create Realtime Prediction Endpoints
        #####################################
        regression_model_id = db('get','{"field_name": "regression_model_id"}')
        if regression_model_id == False:
            #this model is not created yet
            new_msg = {"state": "state_1"}
            publish_to_sns(new_msg, arns[0]['Regression_model'])
        else:
            #start cross validation for regression
            new_msg = {"state": "cv_regression"}
            publish_to_sns(new_msg, arns[0]['Controller'])
        
        multiclass_model_id = db('get','{"field_name": "multiclass_model_id"}')
        if multiclass_model_id == False:
            #this model is not created yet
            new_msg = {"state": "state_1"}
            publish_to_sns(new_msg, arns[0]['MultiClass_model'])
        else:
            #start cross validation for multiclass
            new_msg = {"state": "cv_multiclass"}
            publish_to_sns(new_msg, arns[0]['Controller'])
        
    if curr_state == 'cv_multiclass':
        #####################################
        # trigger Multiclass Cross Validation
        #####################################
        #if you don't pass prefix, it will set to current date (year-month-day_) by default. you can send it by message. use "prefix": "my prefix"
        #data_s3_url = "s3://testlogs2017/export_to_csv/17-06-14-11-40-49.csv"
        #data_s3_url = "s3://"+bucket+dataset_dir
        #"multiclass.csv.schema" #it will use local schema in lambda directory
        new_msg = {"state": "state_1"}
        publish_to_sns(new_msg, arns[0]['CV_MultiClass'])
    
    if curr_state == 'cv_regression':
        #####################################
        # trigger Regression Cross Validation
        #####################################
        #if you don't pass prefix, it will set to current date (year-month-day_) by default. you can send it by message. use "prefix": "my prefix"
        
        # if we are here, it mean we got "Cross Validation Multiclass avarage fscore" from past step
        # we should pass this value to next step (to compare with regression result)
        #cv_multiclass_avg_fscore = json_message['cv_multiclass_avg_fscore']

        #data_s3_url = "s3://"+bucket+dataset_dir
        #"regression.csv.schema" #it will use local schema in lambda directory
        new_msg = {"state": "state_1"}
        publish_to_sns(new_msg, arns[0]['CV_Regression'])
        
    if curr_state == 'compare':
        #####################################
        # compare Regression Cross Validation
        # with MultiClass Cross Validation
        #####################################
        print (":::::::::::::::START COMPARING:::::::::::::::::")
        cv_regression_avg_rmse = float(db('get','{"field_name": "cv_regression_avg_rmse"}'))
        cv_multiclass_avg_fscore = float(db('get','{"field_name": "cv_multiclass_avg_fscore"}'))
        
        if cv_regression_avg_rmse and cv_multiclass_avg_fscore:
            print ("Compare Cross Validation Regression ("+str(cv_regression_avg_rmse)+") to Cross Validation Multiclass ("+str(cv_multiclass_avg_fscore)+")")
            #regression and multiclass set their cross validation's result
            
            regression_percent = (1 - cv_regression_avg_rmse) * 100
            multiclass_percent = cv_multiclass_avg_fscore * 100
            
            print ("Regression accuracy: "+ str(regression_percent))
            print ("MultiClass accuracy: "+ str(multiclass_percent))
            
            margin = regression_percent - multiclass_percent
            
            if margin > 0:
                print ("Regression is better than Multiclass in "+str(margin)+"%")
                using = 'Regression'
            else:
                print ("Multiclass is better than Regression in "+str(-1 * margin)+"%")
                using = 'Multiclass'
                
            db('insert','{"field_name": "compare_result", "field_value": "'+using+'"}')
                
            print("From Now Until next comparing, prediction should use >>>>>>>>>> "+using)
            
            #new_msg = {"state": "state_1"}
            #publish_to_sns(new_msg, arns[0]['RealTimePrediction'])
        else:
            #at end of model creation each of multiclass or regression will request to compare
            #then if of them is not ready now, it mean it's model is working yet and it will
            #send request later.
            if cv_regression_avg_rmse == False:
                print ("waiting for Regression Cross Validation result to start comparing.")
            else:
                print ("waiting for Multiclass Cross Validation result to start comparing.")

def is_database_ready(dynamodb_table_name):
    dynamodb = boto3.resource('dynamodb')
    created_now = False
    created_before = False
    try:
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
            
        table.meta.client.get_waiter('table_exists').wait(TableName=dynamodb_table_name)
        created_now = True
        
    except ClientError as e:
        if 'Table already exists' in e.message:
            created_before = True
            print ('Table is already exists, continuing to poll ...')
        else:
            print ('Something is wrong to create a Database')
            print (e.response['Error']['Message'])
            created_now = False
        
    if created_before:
        return 'has_been_exist'
    if created_now:
        return 'is_created'
    else:
        return False

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
        
def publish_to_sns(message, arn):
    if arn == '':
        #use default arn (Controler SNS)
        arn = str(arns[0]["Controller"])
        
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