import time
import datetime
import storage
#import xlsxwriter
import threading
import json
import requests
import os
import csv

def ExportExcel():
    ###############
    ## Set Timer ##
    ###############
    #threading.Timer(1.0, ExportExcel).start()
    
    rest_json = {}
    global directory_name
    exp_path = 'NDBench_export_to_csv/'
    if not os.path.exists(exp_path):
       os.makedirs(exp_path)

    global stored_statistics_name
    stored_statistics_name = "NDBench_Metrics.txt"
    file_name = 'Ndbench_'+str(datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S"))+'.csv'

    csv_heaader_row = {}
    temp_json = {}
    conn = storagetinys3.Connection('*****************','************************************',tls=True)
    
    ###########################
    ## Get Stored Statistics ##
    ###########################
    old_content = requests.get('https://s3.amazonaws.com/multiple-targets/'+exp_path+stored_statistics_name)
    if old_content.status_code ==  200 and len(old_content.content) > 0:
        print stored_statistics_name+' loaded Completely in LOCAL MACHINE'
        
        ########################################
        ## Delete Stored Statistics in Server ##
        ########################################
        # Build Excel file may take few seconds (or minutes)
        # then it's better to clean 'stored_statistics_name' after reading it's data
        # then 'stored_statistics_name' is ready to get new json data
        # to do this, we will build and EMPTY 'stored_statistics_name' file and overwide it
        file = open(stored_statistics_name,'w+')
        ###########conn.upload(stored_statistics_name,file,'multiple-targets')
        os.remove(stored_statistics_name)
        print stored_statistics_name+' deleted from SERVER'

        #####################
        ## Load Statistics ##
        #####################
        json_result = json.loads('['+old_content.content+']')
        
        for row in json_result:
            ############################################
            ## Doing a loop on each row of statistics ##
            ############################################
            '''target = 'low'
            average = float(row['Average'])

            if 30 < average and average <= 70:
                target = 'normal'
            elif 70 < average:
                target = 'high'
            '''
            timestamp = str(row['Timestamp']) #2017-12-03 11-32-57 #2017-05-29 20:18:00+00:00
            try:
                temp_json[timestamp]
            except KeyError:
                temp_json[timestamp] = {}

            #temp_json[timestamp]['Timestamp'] = row['Timestamp']
            temp_json[timestamp]['Date'] = timestamp[0:10]
            temp_json[timestamp]['Time'] = timestamp[11:19]
            temp_json[timestamp]['readRPS'] = row['readRPS']
            temp_json[timestamp]['readLatAvg'] = row['readLatAvg']
            temp_json[timestamp]['cacheHitRatioInt'] = row['cacheHitRatioInt']
            temp_json[timestamp]['readLatP99'] = row['readLatP99']
            temp_json[timestamp]['cacheHits'] = row['cacheHits']
            temp_json[timestamp]['writeLatAvg'] = row['writeLatAvg']
            temp_json[timestamp]['readLatP95'] = row['readLatP95']
            temp_json[timestamp]['writeFailure'] = row['writeFailure']
            temp_json[timestamp]['readLatP50'] = row['readLatP50']
            temp_json[timestamp]['readSuccess'] = row['readSuccess']
            temp_json[timestamp]['cacheMiss'] = row['cacheMiss']
            temp_json[timestamp]['writeLatP50'] = row['writeLatP50']
            temp_json[timestamp]['writeRPS'] = row['writeRPS']
            temp_json[timestamp]['writeLatP95'] = row['writeLatP95']
            temp_json[timestamp]['writeSuccess'] = row['writeSuccess']
            temp_json[timestamp]['writeLatP99'] = row['writeLatP99']
            temp_json[timestamp]['writeLatP995'] = row['writeLatP995']
            temp_json[timestamp]['readFailure'] = row['readFailure']
            temp_json[timestamp]['writeLatP999'] = row['writeLatP999']
            #temp_json[timestamp]['documentation'] = row['documentation']
            temp_json[timestamp]['readLatP995'] = row['readLatP995']
            temp_json[timestamp]['readLatP999'] = row['readLatP999']
        
    ########################
    ## start creating CSV ##
    ########################
    final_header = ['Date', 'Time', 'readRPS', 'readLatAvg', 'cacheHitRatioInt', 'readLatP99', 'cacheHits', 'writeLatAvg', 'readLatP95', 'writeFailure', 'readLatP50', 'readSuccess', 'cacheMiss', 'writeLatP50', 'writeRPS', 'writeLatP95', 'writeSuccess', 'writeLatP99', 'writeLatP995', 'readFailure', 'writeLatP999', 'readLatP995', 'readLatP999']
    with open(exp_path+file_name, 'w') as csvfile:
        #set final_header to CSV's header and add posibility to be able to 'map' to the CSV's cells
        writer = csv.DictWriter(csvfile, fieldnames=final_header)
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        #csv_writer.writerow(['SampleCount', 'Date', 'Time', 'Average', 'Maximum', 'Minimum', 'Sum', 'Unit', 'Target'])
        
        #rebuild json to sort by timestamp
        rebuild_json_to_sort = []
        
        for key in temp_json:
            rebuild_json_to_sort.append({'Timestamp': key, 'statistics_holder': temp_json[key]})
        
        sorted_json = sorted(rebuild_json_to_sort, key=lambda x : x['Timestamp'], reverse=False)
        
        for key in sorted_json:
            #print json.dumps(key['statistics_holder'])
            writer.writerow(key['statistics_holder'])
        
        print '<'+file_name+'> created in LOCAL MACHINE in: '+exp_path+file_name

    file = open(exp_path+file_name,'rb')
    conn.upload(exp_path+file_name,file,'multiple-targets')
    print '<'+file_name+'> uploaded completely in SERVER in '+exp_path+file_name

    # uploading has been finished and we can remove unnecesary excel file
    try:
       #os.remove(exp_path+file_name)
       print '<'+file_name+'> deleted completely from LOCAL MACHINE'
    except OSError:
       pass
ExportExcel()











