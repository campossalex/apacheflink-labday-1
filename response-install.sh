#!/usr/bin/env bash

PUBLIC_IP=$(curl --silent http://169.254.169.254/latest/meta-data/public-ipv4)

printf "Environment urls:\n\n"
printf "Environment Links: http://$PUBLIC_IP\n"
printf "VVP: http://$PUBLIC_IP:8080\n"
printf "Redpanda: http://$PUBLIC_IP:8085\n"
printf "Grafana: http://$PUBLIC_IP:9090\n"
printf "Web CLI: http://$PUBLIC_IP:4200\n\n"

printf "Environment Public IP:\n"
printf "$PUBLIC_IP\n"
