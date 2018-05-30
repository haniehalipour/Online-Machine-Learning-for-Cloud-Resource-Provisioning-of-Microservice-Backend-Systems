import time
import datetime
import tinys3
#import xlsxwriter
import threading
import json
import requests
import os
import csv
import math

def calculate_final_target(meta_json, weights):
	final_average = 0
	
	for metric in weights:
		try:
			final_average += meta_json[metric+'_Average'] * weights[metric]
		except KeyError:
			#print "Following row dosen't had '"+metric+"_Average'..!"
			#print json.dumps(meta_json)
			return False
	
	final_target = '1'#Low
	if 45 < final_average and final_average <=60:
		final_target = '2'#Normal
	elif 60 < final_average:
		final_target = '3'#High
	
	meta_json['Final_Target'] = final_average
	meta_json['Final_Class'] = final_target

	####################################
	## Replace Network unints in Byte ##
	####################################
	try:
		meta_json['NetworkIn_Average'] = meta_json['temp_networkIn']
		meta_json.pop('temp_networkIn', None) #Remove element cell in json
	except:
		pass
	
	try:
		meta_json['NetworkOut_Average'] = meta_json['temp_networkOut']
		meta_json.pop('temp_networkOut', None) #Remove element cell in json
	except:
		pass
		
	return meta_json
	
def preparation(metric, overview):
	temp_average = float(metric['Average']) / 100
	if temp_average == 0:
		temp_average = 0.0000001
	
	try:
		overview[metric['type']]["normal_sum"] += temp_average
		overview[metric['type']]["count"] += 1
		
		#SET Minimum
		if temp_average < overview[metric['type']]["min"]:
			overview[metric['type']]["min"] = temp_average
		
		#SET Maximum
		if overview[metric['type']]["max"] < temp_average:
			overview[metric['type']]["max"] = temp_average
			
	except KeyError:
		overview[metric['type']] = {}
		overview[metric['type']]["normal_sum"] = temp_average
		overview[metric['type']]["min"] = temp_average
		overview[metric['type']]["max"] = temp_average
		overview[metric['type']]["count"] = 1
		
	return overview

def ExportExcel():
	###############
	## Set Timer ##
	###############
	#threading.Timer(86400.0, ExportExcel).start()
	
	stored_statistics_name = "statistics2.txt"
	main_config = {}
	averages = {}
	overview = {}
	global directory_name
	exp_path = 'export_to_csv/'
	if not os.path.exists(exp_path):
	   os.makedirs(exp_path)

	global file_name
	file_name = str(datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S"))+'.csv'

	#global limiter
	#limiter = 0
	csv_heaader_row = {}
	
	conn = tinys3.Connection('*********************','****************************',tls=True)

	#####################
	## Get Main Config ##
	#####################
	config_file_name = 'main_config.txt'
	print 'Getting OLD "'+config_file_name+'" from multiple-targets (S3)'
	old_config = requests.get('https://s3.amazonaws.com/multiple-targets/'+config_file_name)
	if old_config.status_code == 200 and len(old_config.content) > 0:
		print 'Load OLD "'+config_file_name+'" from multiple-targets (S3), into the current Config'
		main_config = json.loads(old_config.content)
	
	###############################
	## Fore to calculate Wiehgts ##
	###############################
	try:
		del main_config["weights"]
		# Weights has been set before in the old config file
		# No need to calculate Averages
	except KeyError:
		pass
	
	###########################
	## Get Stored Statistics ##
	###########################
	old_content = requests.get('https://s3.amazonaws.com/multiple-targets/'+stored_statistics_name)
	if old_content.status_code ==  200:
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
		temp_json = {}
		#default_headers = ['SampleCount', 'Date', 'Time', 'Average', 'Maximum', 'Minimum', 'Sum', 'Unit', 'Target']
		default_headers = ['Average', 'Target']
		
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
					element['temp_networkIn'] = element['Average']
					element['Average'] = "{0:.2f}".format((element['Average'] * 100) / main_config["network_in_max"])
					#element['Maximum'] = (element['Average'] * 100) / main_config["network_in_max"]
				elif type == "NetworkOut":
					element['temp_networkOut'] = element['Average']
					element['Average'] = "{0:.2f}".format((element['Average'] * 100) / main_config["network_out_max"])
					#element['Maximum'] = (element['Average'] * 100) / main_config["network_out_max"]
				
				overview = preparation(element, overview)
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

				###############temp_json[timestamp][type+'_SampleCount'] = float(element['SampleCount'])
				temp_json[timestamp]['Date'] = timestamp[0:10]
				temp_json[timestamp]['Time'] = timestamp[11:19]
				temp_json[timestamp][type+'_Average'] = float(element['Average'])
				###############temp_json[timestamp][type+'_Maximum'] = float(element['Maximum'])
				###############temp_json[timestamp][type+'_Minimum'] = float(element['Minimum'])
				###############temp_json[timestamp][type+'_Sum'] = float(element['Sum'])
				###############temp_json[timestamp][type+'_Unit'] = str(element['Unit'])
				temp_json[timestamp][type+'_Target'] = target
				
				if type == "NetworkIn":
					temp_json[timestamp]['temp_networkIn'] = element['temp_networkIn']
				elif type == "NetworkOut":
					temp_json[timestamp]['temp_networkOut'] = element['temp_networkOut']
					
				#for each report we have several information (something like SampleCount, Date, Time, Average and ...)
				#we should add these informations close to each other in SCV, then we will add "map" cell for them to our CSV
				#here we just will collect these informations. later we will add them to CSV's header
				#we will do it for each type (for CPUUtilization, DiskReadBytes and ...) of reports
				'''
				output will be something like this:
				{'DiskReadBytes': ['DiskReadBytes_SampleCount', 'DiskReadBytes_Date', 'DiskReadBytes_Time', 'DiskReadBytes_Average', 'DiskReadBytes_Maximum', 'DiskReadBytes_Minimum', 'DiskReadBytes_Sum', 'DiskReadBytes_Unit', 'DiskReadBytes_Target'], 'NetworkIn': ['NetworkIn_SampleCount', 'NetworkIn_Date', 'NetworkIn_Time', 'NetworkIn_Average', 'NetworkIn_Maximum', 'NetworkIn_Minimum', 'NetworkIn_Sum', 'NetworkIn_Unit', 'NetworkIn_Target'], 'DiskWriteBytes': ['DiskWriteBytes_SampleCount', 'DiskWriteBytes_Date', 'DiskWriteBytes_Time', 'DiskWriteBytes_Average', 'DiskWriteBytes_Maximum', 'DiskWriteBytes_Minimum', 'DiskWriteBytes_Sum', 'DiskWriteBytes_Unit', 'DiskWriteBytes_Target'], 'CPUUtilization': ['CPUUtilization_SampleCount', 'CPUUtilization_Date', 'CPUUtilization_Time', 'CPUUtilization_Average', 'CPUUtilization_Maximum', 'CPUUtilization_Minimum', 'CPUUtilization_Sum', 'CPUUtilization_Unit', 'CPUUtilization_Target'], 'NetworkOut': ['NetworkOut_SampleCount', 'NetworkOut_Date', 'NetworkOut_Time', 'NetworkOut_Average', 'NetworkOut_Maximum', 'NetworkOut_Minimum', 'NetworkOut_Sum', 'NetworkOut_Unit', 'NetworkOut_Target']}
				'''
				try:
					csv_heaader_row[type]
				except KeyError:
					csv_heaader_row[type] = []
					for header in default_headers:
						if header in ['Date', 'Time']:
							#temp_index = type+'_'+header
							pass
						else:
							temp_index = type+'_'+header
							csv_heaader_row[type].append(temp_index)


				#temp_json.append({'Timestamp': element['Timestamp'], 'SampleCount': float(element['SampleCount']), 'Date': timestamp[0:10], 'Time': timestamp[11:19], 'Average': float(element['Average']), 'Maximum': float(element['Maximum']), 'Minimum': float(element['Minimum']), 'Sum': float(element['Sum']), 'Unit': str(element['Unit']), 'Target': target})
				#csv_writer.writerow([float(element['SampleCount']), timestamp[0:10], timestamp[11:19], float(element['Average']), float(element['Maximum']), float(element['Minimum']), float(element['Sum']), str(element['Unit']), target])
				#limiter += 1
	
	#build final_header array
	'''
	output for final_header is something like this:
	['DiskReadBytes_SampleCount', 'DiskReadBytes_Date', 'DiskReadBytes_Time', 'DiskReadBytes_Average', 'DiskReadBytes_Maximum', 'DiskReadBytes_Minimum', 'DiskReadBytes_Sum', 'DiskReadBytes_Unit', 'DiskReadBytes_Target', 'NetworkIn_SampleCount', 'NetworkIn_Date', 'NetworkIn_Time', 'NetworkIn_Average', 'NetworkIn_Maximum', 'NetworkIn_Minimum', 'NetworkIn_Sum', 'NetworkIn_Unit', 'NetworkIn_Target', 'DiskWriteBytes_SampleCount', 'DiskWriteBytes_Date', 'DiskWriteBytes_Time', 'DiskWriteBytes_Average', 'DiskWriteBytes_Maximum', 'DiskWriteBytes_Minimum', 'DiskWriteBytes_Sum', 'DiskWriteBytes_Unit', 'DiskWriteBytes_Target', 'CPUUtilization_SampleCount', 'CPUUtilization_Date', 'CPUUtilization_Time', 'CPUUtilization_Average', 'CPUUtilization_Maximum', 'CPUUtilization_Minimum', 'CPUUtilization_Sum', 'CPUUtilization_Unit', 'CPUUtilization_Target', 'NetworkOut_SampleCount', 'NetworkOut_Date', 'NetworkOut_Time', 'NetworkOut_Average', 'NetworkOut_Maximum', 'NetworkOut_Minimum', 'NetworkOut_Sum', 'NetworkOut_Unit', 'NetworkOut_Target']
	'''
	#print averages
	#######################
	## Calculate Weights ##
	#######################
	
	### Entropy Hessam ###
	total_sum = 0
	for key, value in overview.items():
		total_sum += overview[key]["normal_sum"]
		
	normilized_temp_json = {}
	
	for key, value in overview.items():
		overview[key]["h_sum_of_LNs"] = 0
		
	destroyed_rows = 0 #rows that missed some metrics
	for key in temp_json:
		try:
			normilized_temp_json[key]
		except KeyError:
			normilized_temp_json[key] = {}
		
		try:
			temp_json[key]['CPUUtilization_Average']
			temp_json[key]['MemoryUtilization_Average']
			temp_json[key]['NetworkIn_Average']
			temp_json[key]['NetworkOut_Average']
			
			temp = (temp_json[key]['CPUUtilization_Average']/100)/total_sum
			if temp == 0:
				temp = 0.0000001
			temp = temp * math.log(temp)
			normilized_temp_json[key]['CPUUtilization_Average'] = temp
			overview['CPUUtilization']["h_sum_of_LNs"] += temp
			
			temp = (temp_json[key]['MemoryUtilization_Average']/100)/total_sum
			if temp == 0:
				temp = 0.0000001
			temp = temp * math.log(temp)
			normilized_temp_json[key]['MemoryUtilization_Average'] = temp
			overview['MemoryUtilization']["h_sum_of_LNs"] += temp
			
			temp = (temp_json[key]['NetworkIn_Average']/100)/total_sum
			if temp == 0:
				temp = 0.0000001
			temp = temp * math.log(temp)
			normilized_temp_json[key]['NetworkIn_Average'] = temp
			overview['NetworkIn']["h_sum_of_LNs"] += temp
			
			temp = (temp_json[key]['NetworkOut_Average']/100)/total_sum
			if temp == 0:
				temp = 0.0000001
			temp = temp * math.log(temp)
			normilized_temp_json[key]['NetworkOut_Average'] = temp
			overview['NetworkOut']["h_sum_of_LNs"] += temp
		except KeyError:
			print ("Some metrics are missed in this row: {}".format(json.dumps(temp_json[key])))
			destroyed_rows += 1
		
	#print normilized_temp_json
	
	weights = {}
	
	print "All rows: " + str(len(temp_json))
	print "Acceptable rows: " + str(len(temp_json) - destroyed_rows)
	k = 1 / math.log(len(temp_json) - destroyed_rows)
	
	sum_of_entropies = 0
	for key, value in overview.items():
		overview[key]["entropy"] = value['h_sum_of_LNs'] * (-1 * k)
		sum_of_entropies += overview[key]["entropy"]
		
	for key, value in overview.items():
		weights[key] = overview[key]["entropy"] / sum_of_entropies
	
	
	print "overview"
	print json.dumps(overview)
	
	print "weights"
	print json.dumps(weights)
	###########################
	## Upload weights Config ##
	###########################
	try:
		main_config["weights"]
		print 'Weights has been set before in the old config file'
	except KeyError:
		print 'Create new "'+config_file_name+'" in LocalMachine'
		config_file = open(config_file_name,'w+')
		
		main_config["weights"] = weights
		print 'Set weights to the config file'
		config_in_str = json.dumps(main_config)
		config_file.write(config_in_str)
		
		print 'Uploading new "'+config_file_name+'" in multiple-targets (S3)'
		conn.upload(config_file_name, config_file, 'multiple-targets')
		
		try:
			os.remove(config_file_name)
			print '"'+config_file_name+'" deleted completely from LOCAL MACHINE'
		except OSError:
			pass  
	
	
	final_header = ['Date', 'Time'] #date and time for all rows are same
	for row in csv_heaader_row:
		grouped_headers = csv_heaader_row[row]
		for item in grouped_headers:
			final_header.append(item)
	
	#Add Target For Decition Tree
	final_header.append('Final_Target')
	final_header.append('Final_Class')
			
	########################
	## start creating CSV ##
	########################
	with open(exp_path+file_name, 'w') as csvfile:
		#set final_header to CSV's header and add posibility to be able to 'map' to the CSV's cells
		writer = csv.DictWriter(csvfile, fieldnames=final_header)
		csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		writer.writeheader()
		#csv_writer.writerow(['SampleCount', 'Date', 'Time', 'Average', 'Maximum', 'Minimum', 'Sum', 'Unit', 'Target'])
		
		#rebuild json to sort by timestamp
		temp_python_json = json.loads(json.dumps(temp_json))
		
		rebuild_json_to_sort = []
		
		#teeeeeeeeeemp
		
		for key in temp_python_json:
			#print temp_python_json[key]
			#teeeeeeeeeemp = calculate_final_target(temp_python_json[key])
			
			statistics = calculate_final_target(temp_python_json[key], weights)
			if statistics:
				rebuild_json_to_sort.append({'Timestamp': key, 'statistics_holder': statistics})
			
		#random_forest(teeeeeeeeeemp)
		sorted_json = sorted(rebuild_json_to_sort, key=lambda x : x['Timestamp'], reverse=False)
		
		for key in sorted_json:
			#print json.dumps(key['statistics_holder'])
			writer.writerow(key['statistics_holder'])
		'''return True
		for row in sorted_json:
			csv_writer.writerow([row['SampleCount'], row['Date'], row['Time'], row['Average'], row['Maximum'], row['Minimum'], row['Sum'], row['Unit'], row['Target']])
		'''	
		
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











