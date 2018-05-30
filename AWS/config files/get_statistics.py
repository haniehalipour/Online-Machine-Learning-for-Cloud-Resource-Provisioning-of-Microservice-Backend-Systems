import boto3
import boto.s3.connection
import tinys3
import locale
from sys import exit
from argparse import ArgumentParser
from datetime import datetime, timedelta
from operator import itemgetter
from requests import get
from boto3.session import Session
#import xlsxwriter
import threading
import json
import requests 
#import pandas
import os

'''import subprocess
proc = subprocess.Popen('ifconfig', stdout=subprocess.PIPE)
tmp = proc.stdout.read()

print tmp'''

def ClockWatchLog():
    #################return True
    def jsonDefault(object):
       return str(object)
    
    print 'Set timer to 60 seconds'
    threading.Timer(60.0, ClockWatchLog).start()

    print 'Connecting to EC2'
    conn = tinys3.Connection('***************','******************************',tls=True)
    parser = ArgumentParser(description='EC2 load checker')
    parser.add_argument('-w', action='store', dest='warn_threshold', type=float, default=0.85)
    parser.add_argument('-c', action='store', dest='crit_threshold', type=float, default=0.95)
    arguments = parser.parse_args()

    print 'Connecting to CloadWatch'
    session = Session(
          aws_access_key_id= '***************',
          aws_secret_access_key= '******************************',
          region_name='us-east-1')
    cw = session.client('cloudwatch')

    print 'Getting Instance ID'
    instance_id = get('http://169.254.169.254/latest/meta-data/instance-id').content
    #instance_id = "i-0cef87af0e9051064"

    #now = datetime.utcnow()
    #past = now - timedelta(minutes=60)
    #future = now + timedelta(minutes=10)
    
    '''results = cw.list_metrics(
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
    )
    
    print results
    return True
    
    metrics = results['Metrics']
    '''
    #end = datetime.utcnow()
    #start = end - timedelta(hours=12)
    #datetime(2017,11,01, 14,58,45,910078)2017-12-07 17:56:00+00:00
    end = datetime.utcnow() - timedelta(minutes=1)#datetime(2017,11,03, 00,00,00)
    start = end - timedelta(minutes=1)#timedelta(hours=1)#timedelta(minutes=30)# - timedelta(minutes=2)#timedelta(days=1) - timedelta(minutes=2)
    period = 60 #one minute
    
    print "Start Time: " + str(start)
    print "End Time: " + str(end)
    
    '''for row in metrics:
        if row['MetricName'] == 'CPUUtilization':
            datapoints = row.query(start, end, 'Average', 'Percent')
            print len(datapoints)
            print row
        #print row['MetricName']
    
    return True
    '''
    
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
    
    file_name = 'statistics2.txt'
    print 'Create new "'+file_name+'" in LocalMachine'
    file = open(file_name,'w+')
    
    print 'Getting Metric Statistics'
    count = 0;
    
    timestamps = []
    # To determine the maximum NetworkIn and NetworkOut bandwidth, follow this link:
    # https://aws.amazon.com/premiumsupport/knowledge-center/network-throughput-benchmark-linux-ec2/
    #config = {"network_in_max": 2347500000, "network_out_max": 2370000000}
    config = {"network_in_max": 10737418240, "network_out_max": 10737418240}
    temp = {}
    for type in result_types:
        namespace = 'AWS/EC2'
        if type['name'] == 'MemoryUtilization':
            namespace = 'System/Linux'
            
        temp_results = cw.get_metric_statistics(
            Namespace= namespace,
            MetricName= type['name'],
            Unit= type['unit'],
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start,
            EndTime=end,
            Period=period,
            Statistics= type['stat']
        )
        print len(temp_results['Datapoints'])
        temp[type['name']] = temp_results['Datapoints']
        
    
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

    
    
    
    for key, metrics in temp.items():
        datapoints_in_json = json.dumps(metrics, default=jsonDefault)
        if count > 0:
            file.write(',')
            
        file.write(datapoints_in_json)
        count += 1
    
    
    print 'Getting OLD "'+file_name+'" from multiple-targets (S3)'
    old_content = requests.get('https://s3.amazonaws.com/multiple-targets/'+file_name)
    if old_content.status_code == 200 and len(old_content.content) > 0:
        print 'Combining recent statistics with OLD "'+file_name+'" from multiple-targets (S3)'
        file.write(',')
        file.write(old_content.content)
    
    print 'Uploading new "'+file_name+'" in multiple-targets (S3)'
    conn.upload(file_name, file, 'multiple-targets')
    
    try:
       os.remove(file_name)
       print '"'+file_name+'" deleted completely from LOCAL MACHINE'
    except OSError:
       pass

    
    
    config_file_name = 'main_config.txt'
    print 'Create new "'+config_file_name+'" in LocalMachine'
    config_file = open(config_file_name,'w+')

    print 'Getting OLD "'+config_file_name+'" from multiple-targets (S3)'
    temp_config_json = {}
    old_config_content = requests.get('https://s3.amazonaws.com/multiple-targets/'+config_file_name)
    if old_config_content.status_code == 200 and len(old_config_content.content) > 0:
        print 'Compare current Config with OLD "'+config_file_name+'" from multiple-targets (S3)'
        temp_config_json = json.loads(old_config_content.content)
        
        if config["network_in_max"] > temp_config_json["network_in_max"]:
            temp_config_json["network_in_max"] = config["network_in_max"]
            
        if config["network_out_max"] > temp_config_json["network_out_max"]:
            temp_config_json["network_out_max"] = config["network_out_max"]
    
        
    config_in_str = json.dumps(config, default=jsonDefault)
    if old_config_content.status_code == 200 and len(old_config_content.content) > 0:
        config_in_str = json.dumps(temp_config_json, default=jsonDefault)
    
    config_file.write(config_in_str)
    
    print 'Uploading new "'+config_file_name+'" in multiple-targets (S3)'
    conn.upload(config_file_name, config_file, 'multiple-targets')
    
    try:
       os.remove(config_file_name)
       print '"'+config_file_name+'" deleted completely from LOCAL MACHINE'
    except OSError:
       pass
        
    return True
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    
    
    
    cpu_results = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start,
        EndTime=end,
        Statistics=['SampleCount','Average','Sum','Minimum','Maximum']
    )
    
    DiskReadOps_results = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='DiskReadOps',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start,
        EndTime=end,
        Statistics=['SampleCount','Average','Sum','Minimum','Maximum']
    )
    
    DiskWriteOps_results = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='DiskWriteOps',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start,
        EndTime=end,
        Statistics=['SampleCount','Average','Sum','Minimum','Maximum']
    )
    
    NetworkIn_results = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='NetworkIn',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start,
        EndTime=end,
        Statistics=['SampleCount','Average','Sum','Minimum','Maximum']
    )
    
    NetworkOut_results = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='NetworkOut',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start,
        EndTime=end,
        Statistics=['SampleCount','Average','Sum','Minimum','Maximum']
    )
    
    cpu_datapoints = cpu_results['Datapoints']
    DiskReadOps_datapoints = DiskReadOps_results['Datapoints']
    DiskWriteOps_datapoints = DiskWriteOps_results['Datapoints']
    
    for row in cpu_results['Datapoints']:
        print row['Timestamp']
    
    print '#########################'
    
    for row in DiskReadOps_results['Datapoints']:
        print row['Timestamp']
    '''
    print json.dumps(cpu_results['Datapoints'], default=jsonDefault)
    print '#########################'
    print json.dumps(DiskReadOps_results['Datapoints'], default=jsonDefault)
    return True

    results = cw.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=past,
        EndTime=future,
        Period=300,
        Statistics=['SampleCount','Average','Sum','Minimum','Maximum']
    )'''


    datapoints = results['Datapoints']
    #print (results)
    #print (datapoints)
    old_content = requests.get('https://s3.amazonaws.com/testlogs2017/cpu.txt')

    file = open('cpu.txt','w+')

    

    datapoints_in_json = json.dumps(datapoints, default=jsonDefault)
    file.write(datapoints_in_json)

    if old_content.status_code == 200 and len(old_content.content) > 0:
       file.write(',')
       file.write(old_content.content)
    
    ################################conn.upload('cpu.txt',file,'testlogs2017')
    
ClockWatchLog()