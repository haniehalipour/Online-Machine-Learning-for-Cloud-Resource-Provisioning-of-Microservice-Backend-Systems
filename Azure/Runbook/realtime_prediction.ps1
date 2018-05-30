Param(
     [parameter(Mandatory=$true)]
     [object]$json
)

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

# Convert object to actual JSON
$json = $json | ConvertFrom-Json

################################
## Get Lastest row of metrics ##
################################

#######################
## Declare Vatiables ##
#######################
$resourceGroup = "TestResourceGroup2"
$storageAccount = "testresourcegroup234"
#$vm_name = "cpuusagetest"

#$tableName = "WADMetricsPT1HP10DV2S20171007"
#$table_prefix = "WADMetrics"
#$partitionKey = "configuration"

$config_table_name = "config"
$partitionKey = "configuration"

#$resource = Get-AzureRmResource -ResourceGroupName $resourceGroup -ResourceName $vm_name -ResourceType Microsoft.Compute/virtualMachines
#$resource.ResourceId

$saContext = (Get-AzureRmStorageAccount -ResourceGroupName $resourceGroup -Name $storageAccount).Context

#########################
## Create Config Table ##
#########################
$config_table = Get-AzureStorageTable -Name $config_table_name -Context $saContext -ErrorAction SilentlyContinue
if ($config_table.Name -eq $config_table_name)
{
    #"Config table with name '$config_table_name' is exist."
}
else
{
    #"Start creating '$config_table_name' as config table."
    #AzureRmStorageTable -Name $config_table_name -Context $saContext -ErrorVariable has_error -ErrorAction SilentlyContinue
    $new_table = New-AzureStorageTable -Name $config_table_name -Context $saContext -ErrorVariable has_error -ErrorAction SilentlyContinue
    
    if ($has_error)
    {
        #"Creating '$config_table_name' has been stopped because of this error:"
        $has_error[0].Exception.Message
    }
    else
    {
        $config_table = Get-AzureStorageTable -Name $config_table_name -Context $saContext -ErrorAction SilentlyContinue
    }
}

###########################
## Get Configuration Row ##
###########################
$config_row = Get-AzureStorageTableRowByColumnName -columnName 'PartitionKey' -operator Equal -table $config_table -value $partitionKey

if ($config_row.PartitionKey -eq $partitionKey)
{
    #"Config Table row is exist"
}
else
{
    #"Start creating configuration row in '$config_table_name' table."
    $added_row = Add-StorageTableRow -table $config_table -partitionKey $partitionKey -rowKey ([guid]::NewGuid().tostring()) -property @{"compered_until_now"=0;"compare_after"=10;"metrics_table_name"="WADMetricsPT1HP10DV2S20171007"} -ErrorVariable has_error -ErrorAction SilentlyContinue
    
    if (-Not $added_row.Result)
    {
        "Creating '$config_table_name' has been stopped because of this error:"
        $has_error[0].Exception.Message

        exit
    }
    else
    {
        $config_row = Get-AzureStorageTableRowByColumnName -columnName 'PartitionKey' -operator Equal -table $config_table -value $partitionKey
    }
}

#Get-AzureStorageTableRowByCustomFilter -customFilter "PartitionKey eq 'configuration'" -table $table -ErrorAction SilentlyContinue
#$config_row.compare_after


#######################
## Update Config Row ##
#######################
$config_row.compare_after = $json.compare_after
$updated = $config_row | Update-AzureStorageTableRow -table $config_table

$updated_row = Get-AzureStorageTableRowByColumnName -columnName 'PartitionKey' -operator Equal -table $config_table -value $partitionKey
$updated_row.compare_after
