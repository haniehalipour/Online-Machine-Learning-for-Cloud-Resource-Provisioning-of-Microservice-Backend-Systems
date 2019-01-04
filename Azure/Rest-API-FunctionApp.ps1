$appID="****************"
$password="****************"
$tenant="****************"
az login --service-principal -u $appID --password $password --tenant $tenant
$rgname= MLApi
$location= eastus
$vmname= mlvm
$image= mlimg
az group create --name $rgname --location $location
az storage account create --name storage234567 --location $location --resource-group $rgname --sku Standard_LRS
az functionapp create --deployment-source-url https://github.com/haniehalipour/mlapiapp.git --resource-group $rgname --consumption-plan-location $location --name app234567 --storage-account  storage234567
az vm create  --resource-group $rgname  --name $vmname  --image $image  --admin-username ubuntu  --ssh-key-value="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCwf63hCvSXHLaOr9QAR6y4LBj6+pgXFGlNxZ58YYj+bdov6tGh+9uDtUhygU661mgbSW8iLIzop52gPKfV3ZQ8LdLlp+YvLSxFClU3Gz3bq9KXaW5vM5RaUUfIGJW/7v9+jdHLlG79QPSkTvFdetVN5vxM7RvflVuDphG0rz0Dv/8W4uRZHNS12AkjsULuv2VO2YQA5TO9GkELbT1P0lfz7NVKckUy1SHegvvOl9Rzn+B+EsmgPBF+KfKSPHzOeK/rZVyInRamOYY76WjG4A26559CdeUJaP66YQdxBTAMrKrkPA4wXh2Iij9gm9KcpKToWv8IXPj8GZFuRg+mscVh imported-openssh-key"
