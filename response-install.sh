#!/usr/bin/env bash

PUBLIC_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)

echo "Environment urls:"
echo "VVP: http://$PUBLIC_IP:8080"
echo "Redpanda: http://$PUBLIC_IP:8085"
echo "Grafana: http://$PUBLIC_IP:9090"
echo "Web CLI: http://$PUBLIC_IP:4200"

echo "Environment Public IP:"
echo "$PUBLIC_IP"
