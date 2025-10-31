#!/usr/bin/env bash

## This script setup all the base system to run the environment lab or demo

# Install kubctl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Install helm chart
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# Install docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start

# add a dns record to /etc/hosts
echo "127.0.0.1 kubernetes-vm" >> /etc/hosts

# start minikube
sudo minikube start --memory=16G --cpus=5 --force

# Wait for the Kubernetes API server to become available
while ! curl --silent --fail --output /dev/null https://192.168.49.2:8443/api 
do
    sleep 1 
done
