from __future__ import print_function

import base64
import boto3
import json
import os
import datetime
import random
import time

print('LAMBDA: ML REGRESSION START')

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
TRAINING_DATA_S3_URL = "s3://"+ db('get','{"field_name": "bucket"}') + "/" +db('get','{"field_name": "regression_dataset_dir"}')

def publish_to_sns(message, arn, delay):
    time.sleep(delay) #sleep for "delay" second
    if arn == '':
        #use default arn (Controler SNS)
        arn = str(arns[0]["Regression_model"])
        
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

def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    json_message = json.loads(str(message))
    
    curr_state = str(json_message['state'])
    
    print (curr_state + ":::::::")
        
    if curr_state == 'state_1':
        data_s3_url = TRAINING_DATA_S3_URL
        schema_fn = db('get','{"field_name": "regression_schema"}')
        recipe_fn = "recipe.json"
        name = "REGRESSION SAMPLE"
           
        ids = build_model(data_s3_url, schema_fn, recipe_fn, name=name)
        model_id = ids[0]
        eval_id = ids[1]
        
        #update ID's into the database for future usages
        #Please Note Insert will UPDATE!!! data if there is any same data!
        db('insert','{"field_name": "regression_model_id", "field_value": "'+model_id+'"}')
        #we dont need Evaluation ID for long term, then we will delete it at end
        db('insert','{"field_name": "regression_eval_id", "field_value": "'+eval_id+'"}')
        
        #send log message to controller
        new_msg = {"state": "log", "message": "Regression_model State_1: Start Creating Model with ID: "+str(model_id)}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        print("Regression (Model_ID: %s) is Creating" % model_id)
        
        new_msg = {"state": "state_2"}
        publish_to_sns(new_msg, '', 0)
    
    if curr_state == 'state_2':
        model_id = db('get','{"field_name": "regression_model_id"}')
        eval_id = db('get','{"field_name": "regression_eval_id"}')
        ml = boto3.client('machinelearning') 
        
        #send log message to controller
        new_msg = {"state": "log", "message": "Regression_model State_2: Wating for Models to be ready..."}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        
        #poll_until_completed will take so much time to complete, we sshould wait..!
        poll_until_completed(ml, model_id, eval_id, context)
        
    if curr_state == 'state_3':
        model_id = db('get','{"field_name": "regression_model_id"}')
        model_status = str(json_message['model_status'])
        eval_status = str(json_message['eval_status'])
        
        s3_ml_output = 's3://'+db('get','{"field_name": "bucket"}')+'/'+db('get','{"field_name": "regression_ml_output"}')
        if model_status == 'COMPLETED' and eval_status == 'COMPLETED':
            #first go to create endpoints URL
            new_msg = {"state": "state_4"}
            publish_to_sns(new_msg, '', 0)
            #delete EVALUATION ID from database
            db('delete','{"field_name": "regression_eval_id"}')
            
            #create prediction (we can skip this step but we should go to next step to
            #build realtime prediction urls)
            build_model_prediction = db('get','{"field_name": "build_model_prediction"}')
            if build_model_prediction:
                #send log message to controller
                new_msg = {"state": "log", "message": "Regression_model State_3: Start Creating Prediction..."}
                publish_to_sns(new_msg, arns[0]['Controller'], 0)
                
                batch_csv_schema = db('get','{"field_name": "regression_batch_csv_schema"}')
                use_model(model_id, batch_csv_schema, s3_ml_output, TRAINING_DATA_S3_URL)
            
        else:
            #send log message to controller
            new_msg = {"state": "error", "message": "Regression_model State_3: Creation models Failed..!\n\nModel Status: "+model_status+"\nEvaluation Status: "+eval_status}
            publish_to_sns(new_msg, arns[0]['Controller'], 0)
            
            print("Something is wrong, model_status is: " + model_status + " eval_status is: " + eval_status)
        
    if curr_state == 'state_4':
        print ('Regression_model State_4: Start Creating Endpoint URL...')
        #send log message to controller
        new_msg = {"state": "log", "message": "Regression_model State_4: Start Creating Endpoint URL..."}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        model_id = db('get','{"field_name": "regression_model_id"}')
        create_endpoint_url(model_id, context)

def create_endpoint_url(ml_model_id, context):
    ml = boto3.client('machinelearning')
    model = ml.get_ml_model(
        MLModelId=ml_model_id,
        Verbose=True
    )
    
    #create endpoint URL
    response = ml.create_realtime_endpoint(
        MLModelId=ml_model_id
    )
    
    endpoint_status = response['RealtimeEndpointInfo']['EndpointStatus']
    
    if endpoint_status == 'FAILED':
        print ("Regression_model State_4: Creating Status <<FAILED>>..!")
        #send log message to controller
        new_msg = {"state": "error", "message": "Regression_model State_4: Creating Endpoint Status <<FAILED>>..!"}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        return False
    elif endpoint_status in ['NONE', 'UPDATING']:
        print ("Regression_model State_4: Waiting for Endpoint to be ready...")
        #send log message to controller
        new_msg = {"state": "log", "message": "Regression_model State_4: Waiting for Endpoint to be ready..."}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        
        remain_millis = context.get_remaining_time_in_millis()
        if remain_millis < 20000: #if more than 20 seconds remain until timeout
            #send SNS to refresh timout
            new_msg = {"state": "state_4"}
            publish_to_sns(new_msg, '', 0)
        else:
            #we have more than 20 secends before getting timeout
            time.sleep(10) #wait 10 seconds
            #repeat this function again
            create_endpoint_url(ml_model_id, context)
    else:
        print ("Regression_model State_4: Endpoint is ready and URL is saved into the Database...")
        created_endpoint = response['RealtimeEndpointInfo']['EndpointUrl']
        db('insert','{"field_name": "regression_endpoint_url", "field_value": "'+created_endpoint+'"}')
        #send log message to controller
        new_msg = {"state": "log", "message": "Regression_model State_4: Endpoint is ready and URL is saved into the Database..."}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        #start Regression Cross Validating
        new_msg = {"state": "cv_regression"}
        publish_to_sns(new_msg, arns[0]['Controller'], 0)
        return True
        
def build_model(data_s3_url, schema_fn, recipe_fn, name, train_percent=70):
    #Creates all the objects needed to build an ML Model & evaluate its quality.
    ml = boto3.client('machinelearning')
    (train_ds_id, test_ds_id) = create_data_sources(ml, data_s3_url, schema_fn, train_percent, name)
    ml_model_id = create_model(ml, train_ds_id, recipe_fn, name)
    eval_id = create_evaluation(ml, ml_model_id, test_ds_id, name)

    return [ml_model_id, eval_id]


def create_data_sources(ml, data_s3_url, schema_fn, train_percent, name):
    """Create two data sources. One with (train_percent)% of the data,
    which will be used for training. The other one with the remainder of the data,
    which is commonly called the "test set" and will be used to evaluate the quality
    of the ML Model.
    """
    train_ds_id = 'ds-' + base64.b32encode(os.urandom(10))
    spec = {
        "DataLocationS3": data_s3_url,
        "DataRearrangement": json.dumps({
            "splitting": {
                "percentBegin": 0,
                "percentEnd": train_percent
            }
        }),
        "DataSchema": open(schema_fn).read(),
    }
    ml.create_data_source_from_s3(
        DataSourceId=train_ds_id,
        DataSpec=spec,
        DataSourceName=name + " - training split",
        ComputeStatistics=True
    )
    print("Created training data set %s" % train_ds_id)

    test_ds_id = 'ds-' + base64.b32encode(os.urandom(10))
    spec['DataRearrangement'] = json.dumps({
        "splitting": {
            "percentBegin": train_percent,
            "percentEnd": 100
        }
    })
    ml.create_data_source_from_s3(
        DataSourceId=test_ds_id,
        DataSpec=spec,
        DataSourceName=name + " - testing split",
        ComputeStatistics=True
    )
    print("Created test data set %s" % test_ds_id)
    return (train_ds_id, test_ds_id)


def create_model(ml, train_ds_id, recipe_fn, name):
    """Creates an ML Model object, which begins the training process.
The quality of the model that the training algorithm produces depends
primarily on the data, but also on the hyper-parameters specified
in the parameters map, and the feature-processing recipe.
    """
    model_id = 'ml-' + base64.b32encode(os.urandom(10))
    ml.create_ml_model(
        MLModelId=model_id,
        MLModelName=name + " model",
        MLModelType="REGRESSION",  # we're predicting True/False values
        Parameters={
            # Refer to the "Machine Learning Concepts" documentation
            # for guidelines on tuning your model
            "sgd.maxPasses": "100",
            "sgd.maxMLModelSizeInBytes": "104857600",  # 100 MiB
            "sgd.l2RegularizationAmount": "1e-4",
        },
        Recipe=open(recipe_fn).read(),
        TrainingDataSourceId=train_ds_id
    )
    print("Created ML Model %s" % model_id)
    return model_id


def create_evaluation(ml, model_id, test_ds_id, name):
    eval_id = 'ev-' + base64.b32encode(os.urandom(10))
    ml.create_evaluation(
        EvaluationId=eval_id,
        EvaluationName=name + " evaluation",
        MLModelId=model_id,
        EvaluationDataSourceId=test_ds_id
    )
    print("Created Evaluation %s" % eval_id)
    return eval_id

    
"""
Demonstrates how to use an ML Model, by setting the score threshold, 
and kicks off a batch prediction job, which uses the ML Model to 
generate predictions on new data.  This script needs the id of the 
ML Model to use.  It also requires the score threshold.

Useage:
    python use_model.py ml_model_id score_threshold s3_output_url

For example:
    python use_model.py ml-12345678901 0.77 s3://your-bucket/prefix
"""

# The URL of the sample data in S3
def use_model(model_id, schema_fn, output_s3, data_s3url):
    """Creates all the objects needed to build an ML Model & evaluate its quality.
    """
    ml = boto3.client('machinelearning')
    ml.update_ml_model(MLModelId=model_id)
    #print("Set score threshold for %s to %.2f" % (model_id, threshold))
    print("Set score for %s" % (model_id))

    bp_id = 'bp-' + base64.b32encode(os.urandom(10))
    ds_id = create_data_source_for_scoring(ml, data_s3url, schema_fn)
    ml.create_batch_prediction(
        BatchPredictionId=bp_id,
        BatchPredictionName="Batch Prediction for marketing sample",
        MLModelId=model_id,
        BatchPredictionDataSourceId=ds_id,
        OutputUri=output_s3
    )
    print("Created Batch Prediction %s" % bp_id)


def poll_until_completed(ml, model_id, eval_id, context):
    now = str(datetime.datetime.now().time())
    
    model = ml.get_ml_model(MLModelId=model_id)
    model_status = model['Status']
    model_message = model.get('Message', '')
    print("Model %s is %s (%s) at %s" % (model_id, model_status, model_message, now))
    
    evaluation = ml.get_evaluation(EvaluationId=eval_id)
    eval_status = evaluation['Status']
    eval_message = evaluation.get('Message', '')
    print("Evaluation %s is %s (%s) at %s" % (eval_id, eval_status, eval_message, now))
    
    if model_status in ['COMPLETED', 'FAILED', 'INVALID'] and eval_status in ['COMPLETED', 'FAILED', 'INVALID']:
        new_msg = {"state": "state_3", "model_status": model_status, "eval_status": eval_status}
        publish_to_sns(new_msg, '', 0)
        return True
    else:
        remain_millis = context.get_remaining_time_in_millis()
        if remain_millis < 20000: #if more than 20 seconds remain until timeout
            #send SNS to refresh timout
            new_msg = {"state": "state_2"}
            publish_to_sns(new_msg, '', 0)
        else:
            #we have more than 20 secends before getting timeout
            time.sleep(10) #wait 10 seconds
            #repeat this function again
            poll_until_completed(ml, model_id, eval_id, context)


def create_data_source_for_scoring(ml, data_s3url, schema_fn):
    ds_id = 'ds-' + base64.b32encode(os.urandom(10))
    ml.create_data_source_from_s3(
        DataSourceId=ds_id,
        DataSourceName="DS for Batch Prediction %s" % data_s3url,
        DataSpec={
            "DataLocationS3": data_s3url,
            "DataSchema": open(schema_fn).read(),
        },
        ComputeStatistics=False
    )
    print("Created Datasource %s for batch prediction" % ds_id)
    return ds_id