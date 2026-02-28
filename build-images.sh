#!/bin/bash
echo "Construction des images Docker..."
docker build -t cineapi:latest ./cineapi
docker build -t cinefront:latest ./cinefront
echo "Images construites avec succès !"
# On commente ou supprime le push
# docker push chatodo/cineapi:latest
# docker push chatodo/cinefront:latest
echo "Terminé !"