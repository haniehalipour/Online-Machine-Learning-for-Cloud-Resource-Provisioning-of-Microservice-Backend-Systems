workflow controller
{
    #Clear-Host

    #### Import-Module AzureRM.Profile -RequiredVersion 1.0.5
    #### Import-Module AzureRM.Insights -RequiredVersion 1.0.5
    #Import-Module AzureRmStorageTable -RequiredVersion 1.0.0.17
    #Import-Module AzureRmStorageTable
    #Import-Module AzureRM.Resources -RequiredVersion 1.0.5
    #Import-Module AzureRm.StorageTable -RequiredVersion 1.0.5

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
    catch
    {
        if (!$servicePrincipalConnection)
        {
            $ErrorMessage = "Connection $connectionName not found."
            throw $ErrorMessage
        }
        else
        {
            Write-Error -Message $_.Exception
            throw $_.Exception
        }
    }

    #######################
    ## Declare Variables ##
    #######################
    $resourceGroup = "TestResourceGroup2"
    $storageAccount = "testresourcegroup234"
    #$vm_name = "cpuusagetest"
    #$tableName = "WADMetricsPT1HP10DV2S20171007"
    #$table_prefix = "WADMetrics"
    #$partitionKey = "configuration"
    $config_table_name = "config"
    $partitionKey = "configuration"

    ###################
    ## Create Models ##
    ###################
    # We should create models using 'WorkBench' or 'Azure Machine Learning Studio' or our online 'Scikit Machine'.
    # Right now I assume that we are using 'Azure Machine Learning Studio' and we built our webservice using Drag & Drop.
    # Then, assume that we requested to build a model, and the process is finished successfully and the URL of our
    # 'WebService' has been saved in the configuration table in our main storage.
    # Please note these steps should be automate, Later!

    ###################################
    ## Get Prediction WebService URL ##
    ###################################
    #$test_obj = '{"task": "update", "target": "compare_after", "update_to": 6}'
    #$json_str = '{"task": "get", "target": "prediction_webservice_url"}'
    $json_str = '{"task": "get_all"}'
    $vars_str = '{"resourceGroup": "'+$resourceGroup+'", "storageAccount": "'+$storageAccount+'", "config_table_name": "'+$config_table_name+'", "partitionKey": "'+$partitionKey+'"}'
    $vars_str
    $config = config -vars $vars_str -json_req $json_str
    $new_result = InlineScript {
    $config = $Using:config
    "hi"
    $config.my_response.GetType()
    "bye"
    }

    #$new_result
    #$IE = New-Object -TypeName System.Object -Property $config.my_response
    #$IE
    #$formatted = $config.my_response | Out-String
    #$formatted.compare_after
    #$formatted["compare_after"]
    
    #$config.my_response.prediction_webservice_url
    
    ##########################
    ## Get Realtime Metrics ##
    ##########################
    $json_str = '{"task": "get_last_10"}'
    "Before:"
    $config.my_response

    $config = InlineScript {
        $config = $Using:config

        $config.my_response('resourceGroup') = $Using:resourceGroup
        $config.my_response('storageAccount') = $Using:storageAccount
        #$config.my_response('vm_name') = $Using:vm_name
        #$config.my_response('tableName') = $Using:tableName
        #$config.my_response('table_prefix') = $Using:table_prefix
        #$config.my_response('partitionKey') = $Using:partitionKey
        $config.my_response('config_table_name') = $Using:config_table_name
        $config.my_response('partitionKey') = $Using:partitionKey
        ; $config
    }
    "after:"
    $config.my_response
    exit
    $realtime_metrics = get_realtime_metric -vars $config.my_response -json_req $json_str

    $realtime_metrics
}