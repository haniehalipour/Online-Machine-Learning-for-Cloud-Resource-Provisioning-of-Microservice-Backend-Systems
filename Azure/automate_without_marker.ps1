Clear-Host
$StartDate=(GET-DATE)
#########################
## Check Login Session ##
#########################
$needLogin = $true
Try 
{
    $content = Get-AzureRmContext
    if ($content) 
    {
        $needLogin = ([string]::IsNullOrEmpty($content.Account))
    } 
} 
Catch 
{
    if ($_ -like "*Login-AzureRmAccount to login*") 
    {
        $needLogin = $true
    } 
    else 
    {
        throw
    }
}

if ($needLogin)
{
    Login-AzureRmAccount
}

#######################
## Declare Vatiables ##
#######################
$resourceGroup = "VMs" #"TestResourceGroup2"
$storageAccount = "mainvmdiag123" #"testresourcegroup234"
$vm_name = "cpuusagetest"

$tableName = "WADMetricsPT1HP10DV2S20180405"
#$table_prefix = "WADMetrics"
$table_prefix = "WADMetricsPT1HP10DV2S2018"
$partitionKey = "TableEntityDemo"
$network_in_max = 10485760 #10 GigaByte
$network_out_max = 10485760 #10 GigaByte
$target_table_name = "TargetedTable"
$target_partitionKey = "targeted"
$normal_min_threshold = 30
$normal_max_threshold = 70

$output_path = "C:\powershell_output\"

#$resource = Get-AzureRmResource -ResourceGroupName $resourceGroup -ResourceName $vm_name -ResourceType Microsoft.Compute/virtualMachines
#$resource.ResourceId
$connection_string = (az storage account show-connection-string --resource-group $resourceGroup --name $storageAccount | ConvertFrom-Json).connectionString
#az storage metrics show --connection-string $connection_string
#az storage table exists --name "WADMetricsPT1HP10DV2S20171007" --connection-string $connection_string
$table_list = (az storage table list --connection-string $connection_string | ConvertFrom-Json).name
"List of tables in selected storage:"
$table_list
""
$db_records = @{}
if ($table_list.Length -eq 0)
{
    "There is no table in '$storageAccount' storage"
}
else
{
    "There is "+$table_list.Length+" tables stored in $storageAccount."
    ###########################################
    ## Find those tables that stored metrics ##
    ###########################################
    $tables = @()
    Foreach($temp_table_name in $table_list)
    {
        if ($temp_table_name.StartsWith($table_prefix))
        {
            $tables += $temp_table_name
        }
    }

    if ($tables.Length -eq 0)
    {
        "There is no table starting with '$table_prefix' as prefix in storage ($storageAccount) tables, then we can't detect any Metric."
    }
    else
    {
        ($tables.Length).tostring()+" tables stored metrics"
        Foreach($table in $tables)
        {
            "get metrics from $table"
            #$temp_result = (az storage entity query --table-name $table --connection-string $connection_string --accept "minimal" --filter "CounterName eq '\Memory\PercentUsedMemory' or CounterName eq '\NetworkInterface\BytesReceived' or CounterName eq '\NetworkInterface\BytesTransmitted' or CounterName eq '\Processor\PercentProcessorTime'" --select "TIMESTAMP" "Average" "CounterName" --num-results 1000 | ConvertFrom-Json) #RowKey eq ':005CMemory:005CAvailableMemory__2518793891999999999'
            <#$temp_result = az storage entity query --table-name $table --connection-string $connection_string --accept "minimal" --filter "CounterName eq '\Memory\PercentUsedMemory' or CounterName eq '\NetworkInterface\BytesReceived' or CounterName eq '\NetworkInterface\BytesTransmitted' or CounterName eq '\Processor\PercentProcessorTime'" --select "TIMESTAMP" "Average" "CounterName" --num-results 1000
            #$temp_result
            #$temp_result.GetType().fullname
            $temp_result = [string]$temp_result
            $temp_result = $temp_result | ConvertFrom-Json
            #>
            $is_more_results = 0
            $nextMarker = @{}
            $nextpartitionkey = ""
            $nextrowkey = ""
            #$nextMarker["nextpartitionkey"] = 0
            #$nextMarker.SetValue("nextrowkey",0)
            #$nextMarker = '{"nextpartitionkey": 0, "nextrowkey": 0}' | ConvertFrom-Json
            #$nextMarker.get('nextpartitionkey')
            <#"nextMarker": {
    "nextpartitionkey": "1!260!OjAwMkZzdWJzY3JpcHRpb25zOjAwMkYzMTM1Nzc1YTowMDJEMTA2ZDowMDJENGVmODowMDJEODlhYTowMDJEN2VkYjM2YjRjMzU2OjAwMkZyZXNvdXJjZUdyb3Vwczo
wMDJGVGVzdFJlc291cmNlR3JvdXAyOjAwMkZwcm92aWRlcnM6MDAyRk1pY3Jvc29mdDowMDJFQ29tcHV0ZTowMDJGdmlydHVhbE1hY2hpbmVzOjAwMkZjcHV1c2FnZXRlc3Q-",
    "nextrowkey": "1!76!MjUxODc5NDAwMDU5OTk5OTk5OV9fOjAwNUNQcm9jZXNzb3I6MDA1Q1BlcmNlbnRVc2VyVGltZQ--"
  }#>

            $number_of_results = 10
            Do
            {
                $filter_str = "CounterName eq '\Memory\PercentUsedMemory' or CounterName eq '\NetworkInterface\BytesReceived' or CounterName eq '\NetworkInterface\BytesTransmitted' or CounterName eq '\Processor\PercentProcessorTime'"

                if ($nextpartitionkey -ne "")
                {
                    #"With --marker"
                    $temp_marker = '"nextMarker": ' + ($nextMarker | ConvertTo-Json)
                    $temp_marker
                    $temp_result = az storage entity query --table-name $table --connection-string $connection_string --accept "none" --filter $filter_str --select "TIMESTAMP" "Average" "CounterName" --num-results $number_of_results --marker $temp_marker
                }
                else
                {
                    #"Without --marker"
                    $temp_result = az storage entity query --table-name $table --connection-string $connection_string --accept "none" --filter $filter_str --select "TIMESTAMP" "Average" "CounterName" --num-results $number_of_results
                }

                

                <#if ($nextpartitionkey -ne "")
                {
                "here"
                $filter_str = $filter_str + " and PartitionKey eq '$nextpartitionkey' and RowKey eq '$nextrowkey'"
                }
                else
                {
                "there"
                }#>
                
                #$temp_result = az storage entity query --table-name $table --connection-string $connection_string --accept "minimal" --filter $filter_str --select "TIMESTAMP" "Average" "CounterName" --num-results 50
                #$temp_result = az storage entity query --table-name $table --connection-string $connection_string --accept "minimal" --filter "CounterName eq '\Memory\PercentUsedMemory' or CounterName eq '\NetworkInterface\BytesReceived' or CounterName eq '\NetworkInterface\BytesTransmitted' or CounterName eq '\Processor\PercentProcessorTime'" --select "TIMESTAMP" "Average" "CounterName" --num-results 1000 --marker $nextMarker
                #$temp_result
                #$temp_result.GetType().fullname
                $temp_result = [string]$temp_result
                $temp_result = $temp_result | ConvertFrom-Json
                #($temp_result.items).Length
                $db_records[$db_records.Count] = $temp_result.items
                <#if (($temp_result.nextMarker.nextpartitionkey).Length -gt 0)
                {
                    #there is more items in the requested query
                    $nextpartitionkey = $temp_result.nextMarker.nextpartitionkey
                    $nextrowkey = $temp_result.nextMarker.nextrowkey
                    $nextMarker["nextpartitionkey"] = $nextpartitionkey
                    $nextMarker["nextrowkey"] = $nextrowkey
                    #$nextMarker = $temp_result.nextMarker
                    $is_more_results = 1
                }
                else
                {
                    $is_more_results = 0
                }#>
            } While ($is_more_results -ne 0) 
            
            #$temp_result.items[0].Average
            #($temp_result.items).Length
            <#($temp_result.items).Length
            if (($temp_result.items).Length -eq 1000)
            {
               $temp_result[0]
            }
            
            "nextMarker": {
    "nextpartitionkey": "1!260!OjAwMkZzdWJzY3JpcHRpb25zOjAwMkYzMTM1Nzc1YTowMDJEMTA2ZDowMDJENGVmODowMDJEODlhYTowMDJEN2VkYjM2YjRjMzU2OjAwMkZyZXNvdXJjZUdyb3Vwczo
wMDJGVGVzdFJlc291cmNlR3JvdXAyOjAwMkZwcm92aWRlcnM6MDAyRk1pY3Jvc29mdDowMDJFQ29tcHV0ZTowMDJGdmlydHVhbE1hY2hpbmVzOjAwMkZjcHV1c2FnZXRlc3Q-",
    "nextrowkey": "1!76!MjUxODc5NDAwMDU5OTk5OTk5OV9fOjAwNUNQcm9jZXNzb3I6MDA1Q1BlcmNlbnRVc2VyVGltZQ--"
  }
            #>
        }
    }
}

$metrics = @{}
#$db_records.Count
for ($i=0; $i -lt $db_records.Count; $i++)
{
    $temp_rows = $db_records[$i]
    Foreach($row in $temp_rows)
    {
        #each row has something like below:
        #           Average CounterName                     TIMESTAMP                 etag                                          
        #           ------- -----------                     ---------                 ---- 

        # Get time in AM/PM format
        #$temp_date = [DateTime]::Parse($row.TIMESTAMP).ToString()
        <#
        $temp_date = [DateTime]::Parse($row.TIMESTAMP).ToString("MM/dd/yyyy HH:mm:ss")
        #Convert time to 24 Hours Format
        #$temp_date = "{0:MM/dd/yyyy HH:mm:ss}" -f [datetime]$temp_date
        $temp_date
        $temp_date = [DateTime]::ParseExact($temp_date.Trim(), 'dd/MM/yyyy HH:mm:ss tt',$null)
        $row.TIMESTAMP = $temp_date
        $temp_index = "{0:yyyyMMddHHmmss}" -f [datetime]$temp_date
        #>

        $temp_index = [DateTime]::Parse($row.TIMESTAMP).ToString("yyyyMMddHHmmss")
        $row.TIMESTAMP = [DateTime]::Parse($row.TIMESTAMP).ToString("MM/dd/yyyy HH:mm:ss")
        #Because of this error:
        #=> Cannot convert value  to type "System.Int32". Error: "Value was either too large or too small for an Int32."
        #we need to convert $temp_index to long
        #to know more follow this link:
        #https://p0wershell.com/?tag=system-int32-error-value-was-either-too-large-or-too-small-for-an-int32
        $temp_index = [long]$temp_index

        if ($metrics[$temp_index])
        {
            # this timestamp is registered before
        }
        else
        {
            # it's first time that we meet this timestamp
            $metrics[$temp_index] = @{}
        }
        
        $metric_type = $row.CounterName

        if ($row.CounterName -eq "\Memory\PercentUsedMemory")
        {
            $metric_type = 'memory'
        }

        if ($row.CounterName -eq "\NetworkInterface\BytesReceived")
        {
            $metric_type = 'netin'
            #Convert to percent
            $row.Average = ($row.Average * 100) / $network_in_max
        }
    
        if ($row.CounterName -eq "\NetworkInterface\BytesTransmitted")
        {
            $metric_type = 'netout'
            #Convert to percent
            $row.Average = ($row.Average * 100) / $network_out_max
        }

        if ($row.CounterName -eq "\Processor\PercentProcessorTime")
        {
            $metric_type = 'cpu'
        }

        $metrics[$temp_index][$metric_type] = $row
    }
}

#$metrics
#"***"
#$metrics | Sort-Object -Property name -Descending | gm
$metrics = $metrics.GetEnumerator() | sort -Property name -Descending
#$sorted
#$metrics
#"###"

$prediction_list = [System.Collections.ArrayList]@()

$metrics.GetEnumerator() | % { 
    #"Current hashtable is: $($_.key)"
    if ($_.value.cpu -and $_.value.memory -and $_.value.netin -and $_.value.netout)
    {
        #create a prediction array list
        $arrayID = $prediction_list.Add(@($_.value.cpu.Average, $_.value.netin.Average, $_.value.netout.Average, $_.value.memory.Average))
    }
    else
    {
        #this row of metric is not compelete and we should skip it, because at least one of metrics is missed
    }
    <#$_.value
    Foreach ($item in ($_.value).GetEnumerator())
    {
        "_________"
        $item.Name
        $item.Value
        "_________"
    }#>
}

$realtime_prediction_url = "ttps://ussouthcentral.services.azureml.net/workspaces/services/****************************/execute?api-version=2.0&details=true"
$realtime_prediction_API_key = '****************************************************'

$request_str = ConvertTo-Json @($prediction_list)
#$request_str
$body = '{
  "Inputs": {
    "input1": {
      "ColumnNames": [
        "CPUUtilization_Average",
        "NetworkIn_Average",
        "NetworkOut_Average",
        "MemoryUtilization_Average"
      ],
      "Values": '+$request_str+'
    }
  },
  "GlobalParameters": {}
}'

$response = Invoke-WebRequest -Uri $realtime_prediction_url -Method POST -Body $body -Headers @{ 'Content-Type' = 'application/json'; 'Authorization' = "Bearer " + $realtime_prediction_API_key }
#$response
if ($response.StatusCode -eq 200)
{
    #we have response
    $values = ($response.Content | ConvertFrom-Json).Results.output1.value.Values
    #"Predicted values are:"
    #$values

    ########################################
    ## save predicted valuse into the CSV ##
    ########################################
    $predicted_result_filename = "predicted_results.csv"
    if(![System.IO.File]::Exists($output_path+$predicted_result_filename)){
        "Create $predicted_result_filename in $output_path"
        $created_file = New-Item -Path $output_path -Name $predicted_result_filename -ItemType "file" -Value '' -Force
        Add-Content -Path ($output_path+$predicted_result_filename) -Value '"Final_Target"'
    }
    
    "Append predicted results to $predicted_result_filename in $output_path"
    $values | foreach {
        Add-Content -Path ($output_path+$predicted_result_filename) -Value $_
    }
}
else
{
    "something is wrong. we can't get response from Realtime Prediction Web Service. the status code is '" + ($response.StatusCode).ToString() + "'"
}


#######################
## FUTURE PREDICTION ##
#######################

###########################
## Load Original DataSet ##
###########################
$csv_rows = [System.Collections.ArrayList]@()
$index = 0

$original_dataset = Import-Csv C:\powershell_output\regression_workload.csv
foreach ($row in $original_dataset)
{
    ##################################################
	## Convert Original Dataset to a sortable array ##
	##################################################
    $row | Add-Member -NotePropertyName index -NotePropertyValue $index
    #$row
    #$arrayID = $csv_rows.Add(@{'index'= $index; "distance"= "unknown"; 'statistics_holder'= $row})
    $arrayID = $csv_rows.Add(@($index, "unknown", $row))
    $index += 1
}
#$csv_rows | sort-object @{Expression={$_[0]}; Ascending=$false}

#$csv_rows[0]["statistics_holder"]

############################
## Load Predicted results ##
############################
<#$prediction_result = [System.Collections.ArrayList]@()

$predicted_results = Import-Csv C:\powershell_output\predicted_results.csv
foreach ($row in $predicted_results)
{
    $arrayID = $prediction_result.Add($row.Final_Target)
}#>
$predicted_results = Import-Csv C:\powershell_output\predicted_results.csv
foreach ($PR in $predicted_results)
{
    foreach ($row in $csv_rows)
    {
        ######################################################
		## Calculate Distance for recently predicted record ##
		######################################################
        $pr_tar = $PR.Final_Target
		#$r_tar = $row["statistics_holder"].Final_Target
        $r_tar = $row[2].Final_Target
		
		$distance = [math]::Sqrt([Math]::Pow($pr_tar - $r_tar, 2))
		
		$csv_rows[$row[0]][1] = $distance
    }

    ############################
	## Calculate max distance ##
	############################
    $percent_of_calculation = 0.25 #25%
	#sort by distance
    $sorted_rows_by_distance = $csv_rows | sort-object @{Expression={$_[1]}; Ascending=$false}
    
	#calculate maximum defference minimum and maximum distance
	$deff = $sorted_rows_by_distance[0][1] - $sorted_rows_by_distance[$sorted_rows_by_distance.Count - 1][1]
	$max_dist = $deff * $percent_of_calculation

    #####################
	## Index Neighbors ##
	#####################
	$index_of_neighbors = [System.Collections.ArrayList]@()
	foreach ($row in $csv_rows)
    {
        if ($csv_rows[$row[0]][1] -lt $max_dist)
        {
            #this record is neighbor
			$arrayID = $index_of_neighbors.Add($row[0])
        }
    }
    
    ##########################################################
	## Calculate average for each Neighbors in future_steps ##
	##########################################################
	# I want to know what is the average of distance for each neighbor in future
	# and I have future_steps as a limit to calculate for future.
	$future_steps = 10
	$neighbor_averages = [System.Collections.ArrayList]@()

    foreach ($neighbor in $index_of_neighbors)
    {
		#then, here, 'neighbor' is index of the row in original dataset
		$average = 0
		$nei = $csv_rows[$neighbor][2] #neighbor point => nei
		#csv_rows[0] is something like:
        #cell 0 is index
        #cell 1 is distance
        #cell 2 is metrics in hashtable format
		#@(0, 'unknown', @{'index'= 0; 'CPUUtilization_Average'= '17'; 'MemoryUtilization_Average'= '5.477561981'; 'NetworkIn_Average'= '20633'; 'Final_Target'= '10.31290488'; 'NetworkOut_Average'= '24534'})
		Try
        {
            $nei_tar = $nei.Final_Target
			$r_tar = $csv_rows[$neighbor + 10][2].Final_Target
			
			#distance = math.sqrt( math.pow(nei_cpu - r_cpu, 2) + math.pow(nei_mem - r_mem, 2) + math.pow(nei_ni - r_ni, 2) + math.pow(nei_no - r_no, 2) + math.pow(nei_tar - r_tar, 2) )
			$distance = $r_tar - $nei_tar
			#print ("distance of P" + str(neighbor + 10) + " => " + str(distance))
			#average += distance
			$arrayID = $neighbor_averages.Add($distance)
        }
        Catch
        {
            #print ("Current point is '{}'    Next retrieved point is '{}'    Number of all points '{}'".format(neighbor, neighbor + next_index, len(csv_rows)))
			#pass
            ""
        }
        
        #$average = $average / $future_steps
    }

    #######################################
	## Calculate average of all averages ##
	#######################################
	$final_average = 0
	foreach ($ave in $neighbor_averages)
    {
		$final_average += $ave
    }

    $final_average = $final_average / $neighbor_averages.Count
	"Predecited result (" + $PR.Final_Target.ToString() + ") after 10 minutes should be ("+([double]$PR.Final_Target + [double]$final_average).ToString()+")"
}

####################
## SSH CONNECTION ##
####################
"Open SSH connection"
$VM_public_IP = "*******"
$VM_Username = "ubuntu"
$VM_KeyFile_dir = "C:\path\to\myPrivateKey_rsa"

"Start Connecting to VM using '$VM_public_IP' public IP and '$VM_Username' as username and '$VM_KeyFile_dir' as a KeyFile"
New-SSHSession -ComputerName $VM_public_IP -Credential $VM_Username -KeyFile $VM_KeyFile_dir

######################
## ADD NEW RESOURCE ##
######################
"Add New Resource:"
(Invoke-SSHCommand -Index 0 -Command "sudo  pwsh /root/test.ps1").Output

$EndDate=(GET-DATE)

$difference_time = NEW-TIMESPAN –Start $StartDate –End $EndDate

$difference_time
"#######################"
"## HOW MANY MINUTES? ##"
"#######################"
$difference_time.TotalSeconds / 60

exit



<#$metrics.GetEnumerator() | % { 
    "Current hashtable is: $($_.key)"
    #Write-Host "Value of Entry 1 is: $($_.value["Entry 1"])" 
}#>

#az storage entity query --table-name $tableName --connection-string $connection_string

#az storage entity show --table-name $storageAccount --partition-key --row-key
exit

#$saContext = (Get-AzureRmStorageAccount -ResourceGroupName $resourceGroup -Name $storageAccount).Context

#$table = Get-AzureStorageTable -Name $tableName -Context $saContext
#Get-AzureStorageTableRowByCustomFilter -customFilter "Target eq ''" -table $table -ErrorAction SilentlyContinue

# Adding rows/entities
#Add-StorageTableRow -table $table -partitionKey $partitionKey -rowKey ([guid]::NewGuid().tostring()) -property @{"firstName"="Paulo";"lastName"="Costa";"role"="presenter"}
 
# Getting all rows
#$result = Get-AzureStorageTableRowAll -table $table -ErrorAction SilentlyContinue
#$result = Get-AzureStorageTableRowByColumnName -columnName Average -operator Equal -table $table -value "4.983333333333333"
#Write-Host ($tables | Format-Table | Out-String)

#####################
## Get All Metrics ##
#####################
#(Get-AzureRmMetricDefinition -ResourceId $resource.ResourceId).name
Get-AzureRmMetric -ResourceId $resource.ResourceId -TimeGrain 00:01:00 -DetailedOutput -MetricNames "Network in"
exit
#Get-UsageMetrics -ResourceId $resource.ResourceId
<#
Valid metrics: 
Percentage CPU,Network In,Network Out,Disk Read Bytes,Disk Write Bytes,Disk Read Operations/Sec,Disk Write Operations/Sec,CPU Credits Remaining,CPU Credits 
Consumed,Per Disk Read Bytes/sec,Per Disk Write Bytes/sec,Per Disk Read Operations/Sec,Per Disk Write Operations/Sec,Per Disk QD,OS Per Disk Read 
Bytes/sec,OS Per Disk Write Bytes/sec,OS Per Disk Read Operations/Sec,OS Per Disk Write Operations/Sec,OS Per Disk QD
#>
#az monitor metrics list --resource $resource.ResourceId --metric "Percentage CPU" --aggregation Average Total
az monitor metrics list --resource $resource.ResourceId --metrics "Percentage CPU,Network In,Network Out" --aggregation Average Total
#az monitor metrics list --resource $resource.ResourceId --metrics FunctionExecutionUnits FunctionExecutionCount --aggregation Total --interval PT1H
exit
$metrics = Get-AzureRmMetricDefinition -ResourceId $resource.ResourceId# -MetricNames "BytesSent,CpuTime"
#$metrics
Foreach($Value in $metrics)
{
    $Value.Name
    "----------------------------------------------------------"
}
exit

$metrics = Get-AzureRmMetric -ResourceId $resource.ResourceId -DetailedOutput
$Formatted = Format-MetricsAsTable -Metrics $metrics
"-----------------------------------------------------------------------"
$Formatted
exit
Get-AzureRmMetric -ResourceId $resource.ResourceId -TimeGrain 00:01:00 -DetailedOutput -MetricNames "Requests"
#$metrics = Get-AzureRmMetric -ResourceId $resource.ResourceId -TimeGrain 00:01:00
#$metrics = Get-Metrics -ResourceId $resource.ResourceId -TimeGrain 00:01:00
#$metrics
exit
$Formatted = Format-MetricsAsTable -Metrics $metrics
$Formatted
exit
#####################
## Collect Metrics ##
#####################
$revised_metrics = @{}
$main_indexs = @()
Foreach($Value in $Formatted)
{
    ######################################
    ## Set Index to merge by this index ##
    ######################################
    $timestamp_index = "{0:MM/dd/yyyy HH:mm:ss}" -f [DateTime]::Parse($Value.TimestampUTC)
    
    if ($revised_metrics[$timestamp_index])
    {
        # this timestamp is registered before
    }
    else
    {
        # it's first time that we meet this timestamp
        #"Main index is '$timestamp_index'"
        $revised_metrics[$timestamp_index] = @{}
        #$revised_metrics[$timestamp_index]["TIMESTAMP"] = $timestamp_index
    }

    ######################
    ## Determine Target ##
    ######################
    $temp_target = "Low"
    if ($Value.Average -ge $normal_min_threshold -and $Value.Average -lt $normal_max_threshold)
    {
        $temp_target = "Normal"
    }
    elseif ($Value.Average -ge $normal_max_threshold)
    {
        $temp_target = "High"
    }

    #################################
    ## Collect useful Metrics only ##
    #################################
    $CounterName = $Value.Name
    $CounterName = $CounterName.Substring($CounterName.LastIndexOf("\")+1)
    $revised_metrics[$timestamp_index]["TIMESTAMP"] = $timestamp_index
    $revised_metrics[$timestamp_index][$CounterName] = $Value.Average
    $revised_metrics[$timestamp_index][$CounterName+"Target"] = $temp_target

    <#if (-Not $main_indexs["TIMESTAMP"])
    {
        $main_indexs += ,"TIMESTAMP"
    }

    if (-Not $main_indexs[$CounterName])
    {
        $main_indexs += ,$CounterName
    }

    if (-Not $main_indexs[$CounterName+"Target"])
    {
        $main_indexs += ,$CounterName+"Target"
    }#>
}

<#for ($i=0; $i -lt $revised_metrics.Count; $i++)
{
    $revised_metrics[$i]
}#>

<#$revised_metrics.GetEnumerator() | % { 
    "Current hashtable is: $($_.key)"
    #Write-Host "Value of Entry 1 is: $($_.value["Entry 1"])" 
}#>

# helper to turn PSCustomObject into a list of key/value pairs
function Get-ObjectMembers {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$True, ValueFromPipeline=$True)]
        [PSCustomObject]$obj
    )
    $obj | Get-Member -MemberType NoteProperty | ForEach-Object {
        $key = $_.Name
        [PSCustomObject]@{Key = $key; Value = $obj."$key"}
    }
}

Foreach ($index in $revised_metrics.GetEnumerator())
{
    $temp_Json = $index.Value | ConvertTo-Json
    $temp_str = ""
    $temp_Json | ConvertFrom-Json | Get-ObjectMembers | foreach {
       #$_.key + " and Value is: "+$_.Value
       $temp_str += '"'+$_.key+'"="'+$_.Value+'";'
    }
    $temp_str = "@{"+$temp_str.Substring(0, $temp_str.Length - 1)+"}"
    
    #$json = @{Path="C:\temp"; Filter="*.js"} | ConvertTo-Json
    $hashtable = @{}
    (ConvertFrom-Json $temp_Json).psobject.properties | Foreach { $hashtable[$_.Name] = $_.Value }

    $added = Add-StorageTableRow -table $target_table -partitionKey $target_partitionKey -rowKey ([guid]::NewGuid().tostring()) -property $hashtable

    #$temp_Obj = $temp_Json | ConvertFrom-Json
    #$temp_Obj.GetEnumerator()
    #$temp_Json.GetEnumerator() | % { 
    #    "Current hashtable is: $($_.key)"
    #    #Write-Host "Value of Entry 1 is: $($_.value["Entry 1"])" 
    #}
    #($index.Value).Name# | Select-Object
    #
    #
    <#$item
    $temp_Obj | ForEach-Object -Process {
        $item = $_

        
    }

    $item | ForEach-Object -Process {
        $_
    }#>
    #Foreach ($obj in $temp_Obj)
    #{
    #    $obj | 
    #}
    #$temp_Obj.PsObject.Properties | Select-Object -ExpandProperty Name | ForEach-Object {
    #Write-Host "Keyy : " $_
    #Write-Host "Valuee : " $temp_Obj."$_"
    #}
    #Foreach ($item in $index.Value)
    #{
    #   ( $item | get-member)[-1].Name
    #}
    #Add-StorageTableRow -table $target_table -partitionKey $target_partitionKey -rowKey ([guid]::NewGuid().tostring()) -property @{"test"="1";"Minimum"="yes"}
    #$temp_str = $temp_obj | ConvertFrom-Json
    #Add-StorageTableRow -table $target_table -partitionKey $target_partitionKey -rowKey ([guid]::NewGuid().tostring()) -property @{"name"= "reza"}
}
<#$Formatted = Format-MetricsAsTable -Metrics $Metrics
Foreach($Value in $Formatted) {
    $Value#Export-Csv -Path "C:\Users\hessa\Desktop\metrics.csv" -Input $Value -Append -NoTypeInformation
}#>
exit
<#
#########################################
## Get All Tables which Stored Metrics ##
#########################################
$tables = AzureRmStorageTable\Get-AzureStorageTable -Prefix $table_prefix -Context $saContext
if ($tables.Length -eq 0)
{
    "There is no table starting with '$table_prefix' as prefix in storage's tabels with name '$tableName', then we can't detect any Metric."
}
else
{
    "There is "+$tables.Length+" tabels stored metrics."
    #####################
    ## Collect Metrics ##
    #####################
    $revised_metrics = @{}
    For ($i=0; $i -lt $tables.Length; $i++)
    {
        $temp_table_name = $tables[$i].Name
        "Request for rows in '$temp_table_name'"

        $temp_table = Get-AzureStorageTable -Name $temp_table_name -Context $saContext
        ###########################
        ## Get all Metric's rows ##
        ###########################
        $result = Get-AzureStorageTableRowAll -table $temp_table -ErrorAction SilentlyContinue
        $result[0]
        "Start addig targets to retrieved metrics"
        For ($j=0; $j -lt $result.Length; $j++)
        {
            $etag = $result[$j].Etag

            #$etag = $etag.Substring($etag.IndexOf("'")+1, $etag.LastIndexOf("'") - $etag.IndexOf("'") -1)
            #$etag = $etag.Replace("%3A", ":")
            #$etag = $etag.Substring(0, $etag.Length -1)
            #[DateTime]::Parse($etag).ToString("s")

            #$etag.Substring
            #$result[$j].Timestamp.GetType().FullName #return System.DateTime
            #$timestamp_index = [DateTime]::Parse($result[$j].TIMESTAMP).ToString("s")
            #"*******"
            #"{0:MM/dd/yyyy hh:mm:ss}" -f $result[$j].Timestamp
            #"*******"
            #$timestamp_index = $result[$j].TIMESTAMP.Minute
            $timestamp_index = $etag
            #$timestamp_index = [DateTime]::Parse($result[$j].Etag.FirstAttribute.Value).ToString("s")
            if ($revised_metrics[$timestamp_index])
            {
                # this timestamp is registered before
            }
            else
            {
                # it's first time that we meet this timestamp
                "Main index is '$timestamp_index'"
                $revised_metrics[$timestamp_index] = @{}
                $revised_metrics[$timestamp_index]["TIMESTAMP"] = $result[$j].TIMESTAMP
            }
            
            #$revised_metrics[$timestamp_index]
            ######################
            ## Determine Target ##
            ######################
            $temp_target = "Low"
            if ($result[$j].Average -ge $normal_min_threshold -and $result[$j].Average -lt $normal_max_threshold)
            {
                $temp_target = "Normal"
            }
            elseif ($result[$j].Average -ge $normal_max_threshold)
            {
                $temp_target = "High"
            }

            #################################
            ## Collect useful Metrics only ##
            #################################
            $CounterName = $result[$j].CounterName
            $CounterName = $CounterName.Substring($CounterName.LastIndexOf("\")+1)
            $revised_metrics[$timestamp_index][$CounterName] = $result[$j].Average
            $revised_metrics[$timestamp_index][$CounterName+"Target"] = $temp_target
            
            #$revised_metrics.Count
            #"###########################"
            #if ($result.CounterName -like "\Memory\PercentUsedMemory" -or
            #$result.CounterName -like "\Memory\PercentUsedMemory" -or
            #$result.CounterName -like "\Memory\PercentUsedMemory" -or
            #$result.CounterName -like "\Memory\PercentUsedMemory")
            #{
            #}
            

            #Add-StorageTableRow -table $target_table -partitionKey $target_partitionKey -rowKey ([guid]::NewGuid().tostring()) -property @{"TIMESTAMP"=$result[$j].TIMESTAMP;"Minimum"=$result[$j].Minimum;"Maximum"=$result[$j].Maximum;"Last"=$result[$j].Last;"Average"=$result[$j].Average;"Total"=$result[$j].Total;"Count"=$result[$j].Count;"Target"=$temp_target}
        }
        $revised_metrics.Count
        $revised_metrics["10/16/2017 21:00:00"].Count
        $keys = $revised_metrics.Keys# | % { "key = $_ , value = " + $revised_metrics.Item($_) }
        Foreach ($key in $keys)
        {
            #$revised_metrics[$key]
            #"############################"
        }
        Foreach ($row in $revised_metrics.GetEnumerator())
        {
            #$row.Value
        }
    }
}#>