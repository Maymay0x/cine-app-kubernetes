#!/bin/bash
echo "Construction des images Docker..."
docker build -t maymay1008/cineapi:latest ./cineapi
docker build -t maymay1008/cinefront:latest ./cinefront
echo "Terminé !"