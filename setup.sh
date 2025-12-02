#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

HELM=${HELM:-helm}
VVP_CHART=${VVP_CHART:-}
VVP_CHART_VERSION=${VVP_CHART_VERSION:-"5.8.1"}

VVP_NAMESPACE=${VVP_NAMESPACE:-vvp}
JOBS_NAMESPACE=${JOBS_NAMESPACE:-"vvp-jobs"}

usage() {
  echo "This script installs Ververica Platform as well as its dependencies into a Kubernetes cluster using Helm."
  echo
  echo "Usage:"
  echo "  $0 [flags]"
  echo
  echo "Flags:"
  echo "  -h, --help"
  echo "  -e, --edition [community|enterprise] (default: commmunity)"
  echo "  -m, --with-metrics"
  echo "  -l, --with-logging"
}

create_namespaces() {
  # Create the vvp system and jobs namespaces if they do not exist
  kubectl get namespace "$VVP_NAMESPACE" > /dev/null 2>&1 || kubectl create namespace "$VVP_NAMESPACE"
  kubectl get namespace "$JOBS_NAMESPACE" > /dev/null 2>&1 || kubectl create namespace "$JOBS_NAMESPACE"
}

helm_install() {
  local name chart namespace

  name="$1"; shift
  chart="$1"; shift
  namespace="$1"; shift

  $HELM \
    --namespace "$namespace" \
    upgrade --install "$name" "$chart" \
    "$@"
}

install_minio() {
  helm \
    --namespace "vvp" \
    upgrade --install "minio" "minio" \
    --repo https://charts.helm.sh/stable \
    --values /root/ververica-platform-playground/setup/helm/values-minio.yaml
}

install_grafana() {
  helm_install grafana grafana "$VVP_NAMESPACE" \
    --repo https://grafana.github.io/helm-charts \
    --values /root/ververica-platform-playground/setup/helm/values-grafana.yaml
}

helm_install_vvp() {
  if [ -n "$VVP_CHART" ];  then
    helm_install vvp "$VVP_CHART" "$VVP_NAMESPACE" \
      --version "$VVP_CHART_VERSION" \
      --values /root/ververica-platform-playground/setup/helm/values-vvp.yaml \
      --set rbac.additionalNamespaces="{$JOBS_NAMESPACE}" \
      --set vvp.blobStorage.s3.endpoint="http://minio.$VVP_NAMESPACE.svc:9000" \
      "$@"
  else
    helm_install vvp ververica-platform "$VVP_NAMESPACE" \
      --repo https://charts.ververica.com \
      --version "$VVP_CHART_VERSION" \
      --values /root/ververica-platform-playground/setup/helm/values-vvp.yaml \
      --set rbac.additionalNamespaces="{$JOBS_NAMESPACE}" \
      --set vvp.blobStorage.s3.endpoint="http://minio.$VVP_NAMESPACE.svc:9000" \
      "$@"
  fi
}

prompt() {
  local yn
  read -r -p "$1 (y/N) " yn

  case "$yn" in
  y | Y)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

install_vvp() {
  local edition install_metrics install_logging helm_additional_parameters

  edition="$1"
  install_metrics="$2"
  install_logging="$3"
  helm_additional_parameters=
  
  # try installation once (aborts and displays license)
  helm_install_vvp $helm_additional_parameters

  echo "Installing..."
  helm_install_vvp \
    --set acceptCommunityEditionLicense=true \
     $helm_additional_parameters
}

main() {
  local edition install_metrics install_logging

  # defaults
  edition="community"
  install_metrics=
  install_logging=

  # parse params
  while [[ "$#" -gt 0 ]]; do case $1 in
    -e|--edition) edition="$2"; shift; shift;;
    -m|--with-metrics) install_metrics=1; shift;;
    -l|--with-logging) install_logging=1; shift;;
    -h|--help) usage; exit;;
    *) usage ; exit 1;;
  esac; done

  # verify params
  case $edition in
    "enterprise"|"community")
      ;;
    *)
      echo "ERROR: unknown edition \"$edition\""
      echo
      usage
      exit 1
  esac

  echo "> Setting up Ververica Platform Playground in namespace '$VVP_NAMESPACE' with jobs in namespace '$JOBS_NAMESPACE'"
  echo "> The currently configured Kubernetes context is: $(kubectl config current-context)"

  echo "> Creating Kubernetes namespaces..."
  create_namespaces

  echo "> Installing Grafana..."
  install_grafana || :
    
  echo "> Installing MinIO..."
  install_minio || :

  echo "> Installing Ververica Platform..."
  install_vvp "$edition" "$install_metrics" "$install_logging" || :

  echo "> Waiting for all Deployments and Pods to become ready..."
  kubectl --namespace "$VVP_NAMESPACE" wait --timeout=5m --for=condition=available deployments --all
  kubectl --namespace "$VVP_NAMESPACE" wait --timeout=5m --for=condition=ready pods --all

  echo "> Successfully set up the Ververica Platform Playground"

  # Nodeport to access VVP and Grafana from browser
  echo "> Applying NodePort configuration..."
  kubectl patch service vvp-ververica-platform -n vvp -p '{"spec": { "type": "NodePort", "ports": [ { "nodePort": 30002, "port": 80, "protocol": "TCP", "targetPort": 8080, "name": "vvp-np" } ] } }'
  kubectl patch service grafana -n vvp -p '{"spec": { "type": "NodePort", "ports": [ { "nodePort": 30003, "port": 80, "protocol": "TCP", "targetPort": 3000, "name": "grafana-np" } ] } }'
  kubectl patch service minio -n vvp -p '{"spec": { "type": "NodePort", "ports": [ { "nodePort": 30004, "port": 9000, "protocol": "TCP", "targetPort": 9000, "name": "minio-np" } ] } }'

  # port-forward setup
  screen -dmS vvp bash -c 'kubectl --address 0.0.0.0 --namespace vvp port-forward services/vvp-ververica-platform 8080:80'
  screen -dmS grafana bash -c 'kubectl --address 0.0.0.0 --namespace vvp port-forward services/grafana 8085:80'
  screen -dmS minio bash -c 'kubectl --address 0.0.0.0 --namespace vvp port-forward services/minio 9000:9000'

  # Waiting VVP to respond
  echo "> Waiting VVP to be ready..."
  while ! curl --silent --fail --output /dev/null localhost:8080/api/v1/status 
  do
      sleep 1 
  done

  # Create Deployment Target and Session Cluster
  curl -i -X POST localhost:8080/api/v1/namespaces/default/deployment-targets -H "Content-Type: application/yaml" --data-binary "@/root/ververica-platform-playground/vvp-resources/deployment_target.yaml"
  curl -i -X POST localhost:8080/api/v1/namespaces/default/sessionclusters -H "Content-Type: application/yaml" --data-binary "@/root/ververica-platform-playground/vvp-resources/sessioncluster.yaml"
  curl -i -X POST 'localhost:8080/namespaces/v1/namespaces/default:setPreviewSessionCluster' -H 'accept: application/json' -H 'Content-Type: application/json' -d '{"previewSessionClusterName": "sql-editor"}'


main "$@"
