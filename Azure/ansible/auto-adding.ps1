sudo az login -u ******** -p ********
sudo ansible-playbook /root/azure_create_vm.yml -u ubuntu

$publicip = (az vm show -g ndbenchtest -n cassandranew -d --query publicIps -otsv)
(Get-Content /etc/ansible/hosts).replace('{{new_public_ip}}', $publicip+"`n{{new_public_ip}}") | Set-Content /etc/ansible/hosts
$privateip = (az vm show -g ndbenchtest -n cassandranew -d --query privateIps -otsv)
$publicip
$privateip
$extra_vars = "{'seed_ip': '10.0.2.9', 'new_private_ip': "+$privateip.ToString()+", 'new_public_ip': "+$publicip.ToString()+"}"
sudo ansible-playbook /root/auto-config.yaml -u ubuntu --extra-vars=$extra_vars
