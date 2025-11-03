## Instructions to spin up this environment

1. Close this repo  
```console
git clone https://github.com/campossalex/apacheflink-labday-1 apacheflink-labday-1/
``` 
3. Change to the repo directory  
```console
cd apacheflink-labday-1
```
5. Change to following configuration for your setup.   
```console
nano terraform.tfvars
```
- `instance_count`, how many instances you need, default is 1
- `key_name`, the key pair to use to launch the ec2 instances  
5. Then initiate terraform  
```console
terraform init
```
6. Then apply terraform  
```console
terraform apply -auto-approve
```
7. Then apply terraform  
```console
terraform apply -auto-approve
```
