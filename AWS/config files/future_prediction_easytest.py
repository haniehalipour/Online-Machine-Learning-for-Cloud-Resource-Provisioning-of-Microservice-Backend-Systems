import csv
import math

############################
## Declare main variables ##
############################
csv_rows = []
index = 0

###########################
## Load Original DataSet ##
###########################
with open("regression_workload.csv") as csvfile:
	reader = csv.DictReader(csvfile)
	title = reader.fieldnames
	for row in reader:
		#row include:
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
prediction_result = []

with open("predicted_results.csv") as csvfile:
	reader = csv.DictReader(csvfile)
	title = reader.fieldnames
	for row in reader:
		#row include:
		#{'Final_Target': '10.31290488', 'NetworkOut_Average': '24534', 'NetworkIn_Average': '20633', 'CPUUtilization_Average': '17', 'MemoryUtilization_Average': '5.477561981'}
		prediction_result.append(row['Final_Target'])

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
		r_tar = float(row['statistics_holder']["Final_Target"])
		
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
			nei_tar = float(nei["Final_Target"])
			r_tar = float(csv_rows[neighbor + 10]['statistics_holder']["Final_Target"])
			
			#distance = math.sqrt( math.pow(nei_cpu - r_cpu, 2) + math.pow(nei_mem - r_mem, 2) + math.pow(nei_ni - r_ni, 2) + math.pow(nei_no - r_no, 2) + math.pow(nei_tar - r_tar, 2) )
			distance = r_tar - nei_tar
			#print ("distance of P" + str(neighbor + 10) + " => " + str(distance))
			#average += distance
			neighbor_averages.append(distance)
		except:
			#print ("Current point is '{}'    Next retrieved point is '{}'    Number of all points '{}'".format(neighbor, neighbor + next_index, len(csv_rows)))
			pass
			
		#average = average / future_steps
		
	
	#######################################
	## Calculate average of all averages ##
	#######################################
	final_average = 0
	for ave in neighbor_averages:
		final_average += ave
		
	final_average = final_average / len(neighbor_averages)
	print (float(PR) + final_average)















