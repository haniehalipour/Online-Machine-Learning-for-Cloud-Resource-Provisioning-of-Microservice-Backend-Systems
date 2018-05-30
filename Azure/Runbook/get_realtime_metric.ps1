workflow get_realtime_metric
{
    param(
         [parameter(Mandatory=$true)]
         [object]$vars, [string]$json_req
    )
    
    # Convert JSON string to actual JSON OBJECT
    $json_obj = ConvertFrom-Json –InputObject $json_req

    "json object ==>"
    $json_obj

    "Vars ==> "
    $vars

    exit


    $new_result = InlineScript {
        $my_errors = @{}
        $my_response = @{}
        $json_obj = $Using:json_obj
        $vars = $Using:vars
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
                #$my_errors[$my_errors.Count] = $ErrorMessage
                throw $ErrorMessage
            } else{
                $my_errors[$my_errors.Count] = $_.Exception
                Write-Error -Message $_.Exception
                throw $_.Exception
            }
        }

        #######################
        ## Declare Variables ##
        #######################
        $resourceGroup = $vars.resourceGroup #"TestResourceGroup2"
        $storageAccount = $vars.storageAccount #"testresourcegroup234"
        #$vm_name = "cpuusagetest"

        #$tableName = "WADMetricsPT1HP10DV2S20171007"
        #$table_prefix = "WADMetrics"
        #$partitionKey = "configuration"

        $config_table_name = $vars.config_table_name #"config"
        $partitionKey = $vars.partitionKey #"configuration"

        $default_config_row = @{
        "compered_until_now"=0;"compare_after"=10;
        "metrics_table_name"="WADMetricsPT1HP10DV2S20171007";
        "prediction_webservice_url"="https://ussouthcentral.services.azureml.net/workspaces/0bb97819a294436abc072177bcded0f0/services/685cade9e56642b5909aec1ab6729dc4/execute?api-version=2.0&details=true"
        }

        #$resource = Get-AzureRmResource -ResourceGroupName $resourceGroup -ResourceName $vm_name -ResourceType Microsoft.Compute/virtualMachines
        #$resource.ResourceId

        $saContext = (Get-AzureRmStorageAccount -ResourceGroupName $resourceGroup -Name $storageAccount).Context

        #########################
        ## Create Config Table ##
        #########################
        $config_table = Get-AzureStorageTable -Name $config_table_name -Context $saContext -ErrorAction SilentlyContinue
        if ($config_table.Name -eq $config_table_name)
        {
            "Config table with name '$config_table_name' is exist."
        }
        else
        {
            "Start creating '$config_table_name' as config table."
            #AzureRmStorageTable -Name $config_table_name -Context $saContext -ErrorVariable has_error -ErrorAction SilentlyContinue
            $new_table = New-AzureStorageTable -Name $config_table_name -Context $saContext -ErrorVariable has_error -ErrorAction SilentlyContinue
    
            if ($has_error)
            {
                $err_msg = "Creating '$config_table_name' has been stopped because of this error:" + $has_error[0].Exception.Message
                $my_errors[$my_errors.Count] = $err_msg
                Write-Error -Message $err_msg
            }
            else
            {
                $config_table = Get-AzureStorageTable -Name $config_table_name -Context $saContext -ErrorAction SilentlyContinue
            }
        }

        ###########################
        ## Get Configuration Row ##
        ###########################
        $config_row = Get-AzureStorageTableRowByColumnName -columnName "PartitionKey" -operator Equal -table $config_table -value $partitionKey
        #Write-Output $config_row
        if ($config_row.PartitionKey -eq $partitionKey)
        {
            "Config Table row is exist"
        }
        else
        {
            "Start creating configuration row in -$config_table_name- table."
            $added_row = Add-StorageTableRow -table $config_table -partitionKey $partitionKey -rowKey ([guid]::NewGuid().tostring()) -property $default_config_row -ErrorVariable has_error -ErrorAction SilentlyContinue
            #$added_row
            if (-Not $added_row.Result)
            {
                $err_msg = "Adding default configuration values into the -$config_table_name- has been stopped because of this error:" + $has_error[0].Exception.Message
                $my_errors[$my_errors.Count] = $err_msg
                Write-Error -Message $err_msg
            }
            else
            {
                $config_row = Get-AzureStorageTableRowByColumnName -columnName "PartitionKey" -operator Equal -table $config_table -value $partitionKey
            }
        }

        ##############
        ## GET ITEM ##
        ##############
        if ($json_obj.task -eq "get_all")
        {
            ## Request is like this:
            ## {"task": "get_all"}
            ## We Should return all config values ##
            "Retrieving All config values"
            #$my_response = @{"task"="all_config"; "values"=$json_obj.target; "value"=$updated_row.$($json_obj.target)}
            $my_response = $config_row
        }

        if ($json_obj.task -eq "get")
        {
            ## Request is like this:
            ## {"task": "get", "target": "prediction_webservice_url"}
            ## We Should get value of "database_column_name" and return it as response ##
            if ($json_obj.target)
            {
                "Retrieving " + $json_obj.target
                if ($config_row.$($json_obj.target))
                {
                    $my_response = @{"task"="retrieved"; "target"=$json_obj.target; "value"=$config_row.$($json_obj.target)}
                }
                else
                {
                    $err_msg += "Field '"+ $json_obj.target +"' not found"
                    $my_errors[$my_errors.Count] = $err_msg
                    Write-Error -Message $err_msg
                }
            }
            else
            {
                $err_msg += 'You should send your GET request like this: {"task": "get", "target": "database_column_name"}'
                $my_errors[$my_errors.Count] = $err_msg
                Write-Error -Message $err_msg
            }
        }

        #Get-AzureStorageTableRowByCustomFilter -customFilter "PartitionKey eq 'configuration'" -table $table -ErrorAction SilentlyContinue
        #$config_row.compare_after

        #######################
        ## Update Config Row ##
        #######################
        if ($json_obj.task -eq "update")
        {
            ## Request is like this:
            ## {"task": "update", "target": "database_column_name", "update_to": "value"}
            ## We Should Update "database_column_name" to "update_to" into the configuration database ##
            if ($json_obj.target -and $json_obj.update_to)
            {
                "Start Updating " + $json_obj.target + " to " + $json_obj.update_to
                #$config_row.compare_after = $json_obj.compare_after
                $config_row.$($json_obj.target) = $json_obj.update_to
                $updated = $config_row | Update-AzureStorageTableRow -table $config_table

                $updated_row = Get-AzureStorageTableRowByColumnName -columnName "PartitionKey" -operator Equal -table $config_table -value $partitionKey
                $my_response = @{"task"="updated"; "target"=$json_obj.target; "value"=$updated_row.$($json_obj.target)}
            }
            else
            {
                $err_msg += 'You should send your UPDATE request like this: {"task": "update", "target": "database_column_name", "update_to": "value"}'
                $my_errors[$my_errors.Count] = $err_msg
                Write-Error -Message $err_msg
            }
        }


        #######################
        ## Update Config Row ##
        #######################
        <##$properties = @{'compare_after'=$config_row.compare_after + 1}
        #Update-AzureStorageTableRow -entity $properties -table $config_table
        #$updated = $properties | Update-AzureStorageTableRow -table $config_table
        $config_row.compare_after = $config_row.compare_after + 1
        ##$config_row = $config_row.compare_after + 1
        $updated = $config_row | Update-AzureStorageTableRow -table $config_table
        #$updated = $properties | Update-AzureStorageTableRow -table $config_table
        #>
        <#$json_obj.compare_after
        if ($json_obj.compare_after)
        {
            "Start Updating Compare_After"
            $config_row.compare_after = $json_obj.compare_after
            $updated = $config_row | Update-AzureStorageTableRow -table $config_table
        }

        $updated_row = Get-AzureStorageTableRowByColumnName -columnName "PartitionKey" -operator Equal -table $config_table -value $partitionKey
        $updated_row.compare_after
        #>

        <#
        ## Test Call another! runbook with passing parameters ##
        $temp_jsonFilePath = "C:\Windows\Temp\temp_json.json"

        $temp_json_str = "{
           "compare_after" : 1
        }"

        $temp_json_str | Out-File -FilePath $temp_jsonFilePath

        $json = (Get-content -path $temp_jsonFilePath -Raw) | Out-string
        $JsonParams = @{"json"=$json}
        $RBParams = @{ AutomationAccountName = "AATest" ResourceGroupName = "RGTest" Name = "Test-Json" Parameters = $JsonParams }
        #>
        $result = @{"my_response"=$my_response; "my_errors"=$my_errors}
        ; $result
    }
    #$new_result.my_response
    
    #Write-Output @{"response"=$json_obj.task}
    Write-Output $new_result

}