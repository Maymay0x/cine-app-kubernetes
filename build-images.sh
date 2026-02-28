#!/bin/bash
echo "Construction des images Docker..."
docker build -t cineapi:latest ./cineapi
docker build -t cinefront:latest ./cinefront
echo "Images construites avec succès !"
echo "Terminé !"