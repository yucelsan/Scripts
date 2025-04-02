#!/bin/bash

# ================================
# Script: create-instance-scaleway.sh
# Description: Crée une instance scaleway avec Block Storage 5K + IP
# ================================

# set -e

# Répertoires
SCRIPT_DIR="$(dirname "$0")"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/log-scaleway-$(date +%Y%m%d-%H%M%S).txt"

# Charger les variables d'environnement
source "$SCRIPT_DIR/.env"

# Logger stdout + stderr
exec > >(tee -a "$LOG_FILE") 2>&1

# --- Début ---
echo -e "\n Démarrage du script de création - $(date)"

VOLUME_NAME="${INSTANCE_NAME}-volume-$(date +%Y%m%d-%H%M%S)"

# --- Création du volume ---
echo -e "\n Création du volume $VOLUME_NAME (Block Storage 5K)"
VOLUME_ID=$(scw instance volume create name="$VOLUME_NAME" volume-type=b_ssd size=10GB zone="$SCW_ZONE" --output json | jq -r '.volume.id')

if [[ -z "$VOLUME_ID" || "$VOLUME_ID" == "null" ]]; then
  echo "ERREUR : le volume n'a pas été créé. Abandon."
  exit 1
fi

echo "Volume créé : $VOLUME_NAME (ID : $VOLUME_ID)"

# --- Création de l'instance ---
echo -e "\n Création de l'instance $INSTANCE_NAME avec volume attaché"
NEW_INSTANCE_ID=$(scw instance server create \
  name="$INSTANCE_NAME" \
  image="$INSTANCE_IMAGE" \
  type="$INSTANCE_TYPE" \
  zone="$SCW_ZONE" \
  dynamic-ip-required=true \
  tags.0="auto-recreated" \
  --output json | jq -r '.id')

echo " Nouvelle instance ID : $NEW_INSTANCE_ID"

# --- Attente de l'activation ---
echo -e "\n Attente de l'activation de l'instance..."
sleep 25

# --- Récupération IP publique ---
PUBLIC_IP=$(scw instance server get "$NEW_INSTANCE_ID" zone="$SCW_ZONE" --output json | jq -r '.public_ip.address')
echo "IP Publique : $PUBLIC_IP"

# --- Mise à jour automatique du .env ---
echo "Mise à jour du .env avec les nouvelles valeurs..."

# On reconstruit le .env
sed -i "s/^INSTANCE_ID=.*/INSTANCE_ID=\"$NEW_INSTANCE_ID\"/" "$SCRIPT_DIR/.env"
sed -i "s/^SCW_IP=.*/SCW_IP=$PUBLIC_IP/" "$SCRIPT_DIR/.env"

# --- Déploiement docker-compose (optionnel) ---
# echo "Copie et déploiement docker-compose frontend/backend..."
# scp -i "$SSH_KEY_PATH" -r ./frontend ./backend root@$PUBLIC_IP:/opt/
# ssh -i "$SSH_KEY_PATH" root@$PUBLIC_IP "cd /opt/frontend && docker-compose up -d && cd /opt/backend && docker-compose up -d"

# --- Fin ---
echo -e "\n Script terminé - $(date)"
echo "Log créé ici : $LOG_FILE"
