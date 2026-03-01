#!/bin/bash
echo "Accès à l'application: https://localhost:8443"
kubectl -n istio-system port-forward deployment/istio-ingressgateway 8443:8443
