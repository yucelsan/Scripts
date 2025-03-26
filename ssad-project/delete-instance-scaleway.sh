#!/bin/bash

# Config serveur Scaleway - Supprime une instance Scaleway via une vm distante.
INSTANCE_NAME="yucelsan-infra"
ZONE="fr-par-1"

echo "🔍 Recherche de l'ID de l'instance : $INSTANCE_NAME"

INSTANCE_ID=$(scw instance server list zone="$ZONE" name="$INSTANCE_NAME" --output json | jq -r '.[0].id')

echo "Arrêt de l'instance $INSTANCE_NAME..."
scw instance server stop "$INSTANCE_ID" zone="$ZONE"

echo "Attente de l'arrêt complet de l'instance..."
sleep 30

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "null" ]; then
  echo "❌ Impossible de trouver l'ID pour $INSTANCE_NAME dans la zone $ZONE"
  exit 1
fi

echo "✅ Instance trouvée : ID = $INSTANCE_ID"
echo "🗑️ Suppression de l'instance..."

scw instance server delete "$INSTANCE_ID" zone="$ZONE" --debug

if [ $? -eq 0 ]; then
  echo "✅ Suppression réussie !"
else
  echo "❌ La suppression a échoué."
fi
