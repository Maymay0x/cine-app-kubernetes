#!/bin/bash
echo "Accès à l'application: http://localhost:8081"
kubectl -n istio-system port-forward deployment/istio-ingressgateway 8081:8080