import csv
from random import randint
import math

##################
## dataset_name ##
##################
# Dataset should be in CSV format and include 4 clomuns include:
# CPU (in percent)
# Network IN (in Bytes)
# Network Out (in Bytes)
# Memory (in Percent)
dataset_name = 'original_dataset.csv'

# Result file will save/overwrite on a file with the following name
output_file_name = "normilized_dataset.csv"

####################
## Column's Names ##
####################
# Order of columns in 'Original Dataset' is not important, but
# you need to set similar names as below in your CSV file,
# Or you can reset bellow names similar to your CSV
cpu_col_name = 'CPUUtilization_Average'
network_in_col_name = 'NetworkIn_Average'
network_out_col_name = 'NetworkOut_Average'
memory_col_name = 'MemoryUtilization_Average'

# Set your network maximum capacity
network_capacity = 10737418240 #10 Gbyte

#################
## Classifying ##
#################
low_threshold = 45 #If "Final target" is less than this percent, it is in low situation
high_threshold = 60 #If "Final target" is higher than this percent, it is in high situation
low_class = 1
normal_class = 2
high_class = 3

originial_dataset = []
with open(dataset_name, newline='') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		originial_dataset.append({"CPU": float(row[cpu_col_name]), "NIN": float(row[network_in_col_name]), "NOUT": float(row[network_out_col_name]), "MEM": float(row[memory_col_name])})

#{'CPU': 24.609750165809583, 'NIN': 126529782.69113044, 'NOUT': 108219655.20444743, 'MEM': 48.57792671629783}

temp_output = []
for i,v in enumerate(originial_dataset):
	network_in = float(v["NIN"])
	network_out = float(v["NOUT"])
	net_in_percent = (network_in * 100) / network_capacity #640000
	net_out_percent = (network_out * 100) / network_capacity #640000
	
	temp_output.append({"cpu": float(v["CPU"]), "original_network_in": network_in, "original_network_out": network_out, "network_in": net_in_percent, "network_out": net_out_percent, "memory": float(v["MEM"])})

###############
## Normilize ##
###############

###################################
## Calculate Sum for each metric ##
###################################
cpu_total_sum = 0
memory_total_sum = 0
network_in_total_sum = 0
network_out_total_sum = 0

for row in temp_output:
	cpu_total_sum += row["cpu"]
	memory_total_sum += row["memory"]
	network_in_total_sum += row["network_in"]
	network_out_total_sum += row["network_out"]
	
total_sum = cpu_total_sum + memory_total_sum + network_in_total_sum + network_out_total_sum

normilized_json = {}
cpu_sum_of_LNs = 0
memory_sum_of_LNs = 0
network_in_sum_of_LNs = 0
network_out_sum_of_LNs = 0

for key,v in enumerate(temp_output):
	try:
		normilized_json[key]
	except:
		normilized_json[key] = {}
		
	temp = (temp_output[key]["cpu"]/100)/total_sum
	if temp == 0:
		temp = 0.0000001
		
	temp = temp * math.log(temp)
	normilized_json[key]["cpu"] = temp
	cpu_sum_of_LNs += temp
	
	temp = (temp_output[key]["memory"]/100)/total_sum
	if temp == 0:
		temp = 0.0000001

	temp = temp * math.log(temp)
	normilized_json[key]["memory"] = temp
	memory_sum_of_LNs += temp
	
	temp = (temp_output[key]['network_in']/100)/total_sum
	if temp == 0:
		temp = 0.0000001

	temp = temp * math.log(temp)
	normilized_json[key]['network_in'] = temp
	network_in_sum_of_LNs += temp
	
	temp = (temp_output[key]['network_out']/100)/total_sum
	if temp == 0:
		temp = 0.0000001

	temp = temp * math.log(temp)
	normilized_json[key]['network_out'] = temp
	network_out_sum_of_LNs += temp
	
weights = {}
k = 1 / math.log(len(normilized_json))
cpu_entropy = cpu_sum_of_LNs * (-1 * k)
memory_entropy = memory_sum_of_LNs * (-1 * k)
network_in_entropy = network_in_sum_of_LNs * (-1 * k)
network_out_entropy = network_out_sum_of_LNs * (-1 * k)

sum_of_entropies = cpu_entropy + memory_entropy + network_in_entropy + network_out_entropy
	
weights['cpu'] = cpu_entropy / sum_of_entropies
weights['memory'] = memory_entropy / sum_of_entropies
weights['network_in'] = network_in_entropy / sum_of_entropies
weights['network_out'] = network_out_entropy / sum_of_entropies

for key,v in enumerate(temp_output):
	temp_final_target = temp_output[key]['cpu'] * weights['cpu'] + temp_output[key]['memory'] * weights['memory'] +  temp_output[key]['network_in'] * weights['network_in'] + temp_output[key]['network_out'] * weights['network_out']

	final_target_class = low_class #Low
	if low_threshold < temp_final_target and temp_final_target <= high_threshold:
		final_target_class = normal_class #Normal
	elif high_threshold < temp_final_target:
		final_target_class = high_class #High

	temp_output[key]['final_target'] = temp_final_target
	temp_output[key]['final_class'] = final_target_class

'''
temp_output[0] is something like this:
{'cpu': 43.934777827115, 'original_network_in': 17428683.557894357, 'original_network_out': 16555721.614524538, 'network_in': 3.492747501058391, 'network_out': 3.31780395835789, 'memory': 43.11890886706646, 'final_target': 42.086168940110326, 'final_class': 1}
'''

f = open(output_file_name, "w")
f.write("{},{},{},{},{},{},{},{}\n".format(cpu_col_name, network_in_col_name+"_original", network_in_col_name, network_out_col_name, network_out_col_name+"_original", memory_col_name,"Final_Target","Final_Class"))
for i,v in enumerate(temp_output):
	f.write("{},{},{},{},{},{},{},{}\n".format(int(v["cpu"]), int(v["original_network_in"]), int(v["network_in"]), int(v["original_network_out"]), int(v["network_out"]), v["memory"], v["final_target"], v["final_class"]))