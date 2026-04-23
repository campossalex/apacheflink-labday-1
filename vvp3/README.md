## Infrastructure
Spin up a m5.4xlarge ec2 instance. This instance has 16 cores and 64 Gb memory. If you need more resources to run Flink jobs, use a m5.8xlarge (32 cores / 128 Gb memory).  

## Minikube, Minio, Mysql and VVP 3.1.0 installation process  

Connect to the instance's command line to run the following commands:  

```
# Additional packaes
sudo yum install -y jq
sudo yum install -y nginx

# Install kubctl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /bin/kubectl

# Install minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /bin/minikube

# Install helm chart
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
sudo HELM_INSTALL_DIR=/bin ./get_helm.sh

# Install docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start

# start minikube
sudo minikube start --memory=40G --cpus=12 --force

# Create ns:

kubectl create ns vvp-system
kubectl create ns vvp-deploy


# Set registry secrets:

kubectl -n vvp-system create secret docker-registry ververica-registry --docker-username=<username> --docker-password=<password> --docker-server=registry.ververica.cloud
kubectl -n vvp-deploy create secret docker-registry vervververica-registry --docker-username=<username> --docker-password=<password> --docker-server=registry.ververica.cloud

# Mysql password secrete

kubectl -n vvp-system create secret generic mysql-secret   --from-literal=mysql-root-password='admin123'

# Deploy mysql
kubectl apply -f values-mysql.yaml

# Deploy minio (s3)
helm --namespace "vvp-system" upgrade --install "minio" "minio" --repo https://charts.helm.sh/stable --values values-minio.yaml

# Deploy the VVP 3 helm

helm upgrade --install ververica-platform oci://registry.ververica.cloud/platform-charts/ververica-platform --version 3.1.0 --namespace vvp-system --values values-vvp.yaml

# Wait the pods to start to the get token

kubectl logs vvp-appmanager-0 -n vvp-system

# Ask for a license to Ververica sendinf the TOKEN obtained before.  
One the license is received, create a license-vvp.yaml with the license content.  

# Upgrade the VVP 3 helm with the license file

helm upgrade --install ververica-platform oci://registry.ververica.cloud/platform-charts/ververica-platform --version 3.1.0 --namespace vvp-system --values values-vvp.yaml -f license-vvp.yaml
```
