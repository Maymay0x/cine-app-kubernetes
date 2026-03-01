#!/bin/bash

kubectl create serviceaccount cineapi-sa
kubectl create serviceaccount cinefront-sa
kubectl create serviceaccount mysql-sa

kubectl create secret generic cinebook-secret \
  --from-literal=host='mysql' \
  --from-literal=username='root' \
  --from-literal=password='rootpassword' \
  --from-literal=db='cinebook'

kubectl apply -f k8s/rbac/service-accounts.yml
kubectl apply -f k8s/rbac/cineapi-rbac.yml
kubectl apply -f k8s/rbac/cinefront-rbac.yml
kubectl apply -f k8s/rbac/mysql-rbac.yml

kubectl apply -f k8s/secret.yml
kubectl apply -f k8s/mysql.yml
echo "Attente MySQL..."
sleep 5
kubectl apply -f k8s/cineapi.yml
kubectl apply -f k8s/cinefront.yml
kubectl apply -f k8s/istio-gateway.yml
kubectl apply -f k8s/mtls/strict-mtls.yml
kubectl apply -f k8s/mtls/destination-rule-mtls.yml