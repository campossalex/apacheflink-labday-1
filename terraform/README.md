## Instructions to spin up this environment

# Prerequisites

- Terraform installed   
- AWS CLI installed  
- Configure aws cli with your aws key credentials  

# Steps  

1. Close this repo  
```console
git clone https://github.com/campossalex/apacheflink-labday-1 apacheflink-labday-1/
``` 
2. Change to the repo directory  
```console
cd apacheflink-labday-1/terraform
```
3. Change to following configuration for your setup.   
```console
nano terraform.tfvars
```
- `instance_count`, how many instances you need, default is 1
- `key_name`, the key pair to use to launch the ec2 instances  
4. Then initiate terraform  
```console
terraform init
```
5. Then apply terraform  
```console
terraform apply -auto-approve
```
6. After the ec2 instances are launched, the public ip address are printed. Copy and paste the address in your web browser to see the welcome page for each instance with the links to access the lab components  

7. Run the following command to tear down the instances   
```console
terraform destroy
```
Type `yes` to confirm the operation.

# Troubleshooting  

If you have issues, ssh to the ec2 instance using the key you configured in the terraform variable and the public ip address:  
```console
ssh -i YOUR_KEY.pem ec2-user@INSTANCE_PUBLIC_ID
```

then check the environment setup log:  
```console
sudo tail -f /var/log/labday_setup.log
```

