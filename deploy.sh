#!/bin/bash
kubectl apply -f k8s/secret.yml
kubectl apply -f k8s/mysql.yml
echo "Attente MySQL..."
sleep 10
kubectl apply -f k8s/cineapi.yml
kubectl apply -f k8s/cinefront.yml
kubectl apply -f k8s/istio-gateway.yml