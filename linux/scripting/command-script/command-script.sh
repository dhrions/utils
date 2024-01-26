#!/bin/bash

while getopts ":f:d:" opt; do
  case $opt in
    f)
      fichier="$OPTARG"
      echo "Option -f avec argument: $fichier"
      # Ajoutez le code que vous souhaitez exécuter pour l'option -f ici
      ;;
    d)
      repertoire="$OPTARG"
      echo "Option -d avec argument: $repertoire"
      # Ajoutez le code que vous souhaitez exécuter pour l'option -d ici
      ;;
    \?)
      echo "Option invalide: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "L'option -$OPTARG nécessite un argument." >&2
      exit 1
      ;;
  esac
done

# Ajoutez le reste du code que vous souhaitez exécuter après le traitement des options ici

