import time
import datetime
import tinys3
#import xlsxwriter
import threading
import json
import requests
import os
import csv

import random
import requests

exp_path = 'NDBench_export_to_csv/'
if not os.path.exists(exp_path):
   os.makedirs(exp_path)
   
file_name = "NDBench_Metrics.txt"
#file_name = str(datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S"))+'.csv'
NdbenchURL = "http://********.*****.azure.com:8080/"
#http://********.*****.azure.com:8080/REST/ndbench/driver/stop
#http://********.*****.azure.com:8080/REST/ndbench/driver/start
#http://********.*****.azure.com:8080/REST/ndbench/config/list

    
def save_ndbench_stats():
    ###############
    ## Set Timer ##
    ###############
    threading.Timer(60.0, save_ndbench_stats).start()
    
    ######################
    ## Get Ndbench Stat ##
    ######################
    print '---------------------------------------'
    print 'Send "getserverstatus" request to REST'
    result = requests.get(NdbenchURL+"REST/ndbench/driver/getserverstatus")
    if result.status_code == 200 and len(result.content) > 0:
        print 'Load "REST Result Content"'
        rest_json = json.loads(result.content)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rest_json['Stats']['Timestamp'] = timestamp
    
    #print json.dumps(rest_json['Stats'])
    conn = tinys3.Connection('**************','**************************',tls=True)
    
    print 'Create new "'+file_name+'" in LocalMachine'
    file = open(exp_path+file_name,'w+')
    file.write(json.dumps(rest_json['Stats']))
    
    print 'Getting OLD "'+file_name+'" from multiple-targets (S3)'
    old_content = requests.get('https://s3.amazonaws.com/multiple-targets/'+exp_path+file_name)
    if old_content.status_code == 200 and len(old_content.content) > 0:
        print 'Combining recent Ndbench statistics with OLD "'+file_name+'" from multiple-targets (S3)'
        file.write(',')
        file.write(old_content.content)
    
    print 'Uploading new "'+file_name+'" in multiple-targets (S3)'
    conn.upload(exp_path+file_name, file, 'multiple-targets', close=True)
    
    try:
       os.remove(file_name)
       print '"'+file_name+'" deleted completely from LOCAL MACHINE'
    except OSError:
       pass
    
save_ndbench_stats()

def generate_new_limit():
    ###############
    ## Set Timer ##
    ###############
    threading.Timer(60.0, generate_new_limit).start()
    
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
    
    #readRateLimit = 10
    #writeRateLimit = 10
    #bool(random.getrandbits(1))
    #conf_json = {"autoTuneEnabled": True, "autoTuneFinalWriteRate": 1001, "autoTuneIncrementIntervalMillisecs": 2, "autoTuneRampPeriodMillisecs": 61, "backfillStartKey": 2, "dataSize": 128, "dataSizeLowerBound": 1002, "dataSizeUpperBound": 5001, "numBackfill": 2, "numKeys": 10001, "numReaders": 5, "numValues": 101, "numWriters": 6, "preloadKeys": True, "readEnabled": True, "readRateLimit": 123, "statsResetFreqSeconds": 201, "statsUpdateFreqSeconds": 6, "useStaticData": True, "useVariableDataSize": True, "writeEnabled": True, "writeRateLimit": 321}
    
    conf_json = {"readRateLimit": readRateLimit, "writeRateLimit": writeRateLimit}
    
    r = requests.post(NdbenchURL+"REST/ndbench/config/set", json=conf_json)
    print ("New limit is '{}':".format(new_limit))
    print (json.dumps(conf_json))
    
generate_new_limit()











