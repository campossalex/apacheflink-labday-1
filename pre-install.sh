#!/usr/bin/env bash

## This script setup all the base system to run the environment lab or demo

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

# Shell In a Box
sudo adduser admin
echo admin:admin1 | chpasswd

yum install shellinabox -y
echo "OPTS="--no-beep --disable-ssl -s /:LOGIN"" >> /etc/sysconfig/shellinaboxd
systemctl start shellinaboxd

# add a dns record to /etc/hosts
echo "127.0.0.1 kubernetes-vm" >> /etc/hosts

# start minikube
sudo minikube start --memory=8G --cpus=5 --force

# Wait for the Kubernetes API server to become available
kubectl --namespace kube-system wait --timeout=5m --for=condition=ready pods --all
