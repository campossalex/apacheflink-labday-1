#!/usr/bin/env bash

PUBLIC_IP=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)

echo "Environment urls:\n"
echo "VVP: http://$IP:8080"
echo "Redpanda: http://$IP:8085"
echo "Grafana: http://$IP:9090"
echo "Web CLI: http://$IP:4200"
