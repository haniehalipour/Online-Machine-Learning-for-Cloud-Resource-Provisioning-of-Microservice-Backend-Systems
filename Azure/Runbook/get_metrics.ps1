Clear-Host

Import-Module AzureRM.Profile -RequiredVersion 1.0.5
Import-Module AzureRM.Insights -RequiredVersion 1.0.5
#Import-Module AzureRmStorageTable

################
## Auto Login ##
################
$connectionName = "AzureRunAsConnection"
 
try
{
    # Get the connection "AzureRunAsConnection "
    $servicePrincipalConnection=Get-AutomationConnection -Name $connectionName         
 
    "Logging in to Azure..."
    Login-AzureRmAccount `
        -ServicePrincipal `
        -TenantId $servicePrincipalConnection.TenantId `
        -ApplicationId $servicePrincipalConnection.ApplicationId `
        -CertificateThumbprint $servicePrincipalConnection.CertificateThumbprint 
}
catch {
    if (!$servicePrincipalConnection)
    {
        $ErrorMessage = "Connection $connectionName not found."
        throw $ErrorMessage
    } else{
        Write-Error -Message $_.Exception
        throw $_.Exception
    }
}


#######################
## Declare Vatiables ##
#######################
$resourceGroup = "TestResourceGroup2"
$storageAccount = "testresourcegroup234"
$vm_name = "cpuusagetest"

$tableName = "WADMetricsPT1HP10DV2S20171007"
$table_prefix = "WADMetrics"
$partitionKey = "TableEntityDemo"

$target_table_name = "TargetedTable"
$target_partitionKey = "targeted"
$normal_min_threshold = 30
$normal_max_threshold = 70

$resource = Get-AzureRmResource -ResourceGroupName $resourceGroup -ResourceName $vm_name -ResourceType Microsoft.Compute/virtualMachines
$resource.ResourceId

exit

$saContext = (Get-AzureRmStorageAccount -ResourceGroupName $resourceGroup -Name $storageAccount).Context
#$table = Get-AzureStorageTable -Name $tableName -Context $saContext
#Get-AzureStorageTableRowByCustomFilter -customFilter "Target eq ''" -table $table -ErrorAction SilentlyContinue

# Adding rows/entities
#Add-StorageTableRow -table $table -partitionKey $partitionKey -rowKey ([guid]::NewGuid().tostring()) -property @{"firstName"="Paulo";"lastName"="Costa";"role"="presenter"}
 
# Getting all rows
#$result = Get-AzureStorageTableRowAll -table $table -ErrorAction SilentlyContinue
#$result = Get-AzureStorageTableRowByColumnName -columnName Average -operator Equal -table $table -value "4.983333333333333"
#Write-Host ($tables | Format-Table | Out-String)

#########################
## Create Target Table ##
#########################
$target_table = Get-AzureStorageTable -Name $target_table_name -Context $saContext -ErrorAction SilentlyContinue
if ($target_table.Name -eq $target_table_name)
{
    "Target table with name '$target_table_name' is exist."
}
else
{
    "Start creating '$target_table_name' as target table."
    AzureRmStorageTable\New-AzureStorageTable -Name $target_table_name -Context $saContext -ErrorVariable has_error -ErrorAction SilentlyContinue
    if ($has_error)
    {
        "Creating '$target_table_name' has been stopped because of this error:"
        $has_error[0].Exception.Message

        exit
    }
    else
    {
        $target_table = Get-AzureStorageTable -Name $target_table_name -Context $saContext -ErrorAction SilentlyContinue
    }
}

#####################
## Get All Metrics ##
#####################
$Metrics = Get-Metrics -ResourceId $resource.ResourceId -TimeGrain 00:01:00
$Metrics
exit

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
    For ($i=0; $i -lt <#$tables.Length#>1; $i++)
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
            <#$etag = $etag.Substring($etag.IndexOf("'")+1, $etag.LastIndexOf("'") - $etag.IndexOf("'") -1)
            $etag = $etag.Replace("%3A", ":")
            $etag = $etag.Substring(0, $etag.Length -1)
            [DateTime]::Parse($etag).ToString("s")#>
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
            <#if ($result.CounterName -like "\Memory\PercentUsedMemory" -or
            $result.CounterName -like "\Memory\PercentUsedMemory" -or
            $result.CounterName -like "\Memory\PercentUsedMemory" -or
            $result.CounterName -like "\Memory\PercentUsedMemory")
            {
            }#>
            

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
}