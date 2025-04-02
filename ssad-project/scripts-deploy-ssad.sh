#!/bin/bash

# ===============================
# Script : scripts-deploy-ssad.sh
# Description : Copie et déploie les services frontend/backend via docker-compose
# ===============================

# Répertoires
SCRIPT_DIR="$(dirname "$0")"
LOG_DIR="$SCRIPT_DIR/logs_copy_script"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/log-scaleway-$(date +%Y%m%d-%H%M%S).txt"

# Charger les variables d'environnement
source "$SCRIPT_DIR/.env"

# Logger stdout + stderr
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Connexion SSH dans notre instance Scaleway..."
ssh -i "$SSH_KEY_PATH" root@$SCW_IP << EOF

mkdir -p /opt/scw_instance_projects

echo "Mise à jour du système..."
apt update && apt upgrade -y

echo "Installation des outils de base..."
apt install -y curl wget git unzip gnupg lsb-release ca-certificates apt-transport-https software-properties-common jq python3 python3-pip emacs vim nginx certbot python3-certbot-nginx

echo "Installation de Ansible..."
apt install ansible

echo "Installation de Docker..."
curl -fsSL https://get.docker.com | bash

echo "Ajout de l'utilisateur root au groupe docker..."
usermod -aG docker root

# Ajouter la clé GPG officielle de HashiCorp pour Terraform
echo "Téléchargement des outils de base pour terraform..."
curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Ajouter le dépôt officiel HashiCorp Terraform
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list

# Mettre à jour les dépôts et installer Terraform
echo "Installation de TERRAFORM ..."
apt update && apt install -y terraform

echo "Installation de Docker Compose (v2)..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r '.tag_name')
curl -SL https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

echo "Rechargement des groupes pour Docker..."
newgrp docker <<EONG

export PATH=\$PATH:/usr/local/bin

echo "Tous les outils ont été installés avec succès !"
echo "Docker : \$(docker --version)"
echo "Docker Compose : \$(docker compose version)"
echo "Terraform : \$(terraform -version | head -n1)"
echo "Ansible : \$(ansible --version | head -n1)"

EONG

EOF

# -- Copie des fichiers docker et ansible --
echo "Copie des dossiers frontend et backend vers $SCW_IP..."
scp -i "$SSH_KEY_PATH" -r /root/scw_instance_projects/yucelsan-devops-test root@$SCW_IP:/opt/scw_instance_projects/
scp -i "$SSH_KEY_PATH" -r /root/scw_instance_projects/yucelsan-devops-deployment root@$SCW_IP:/opt/scw_instance_projects/
scp -i "$SSH_KEY_PATH" -r /root/scw_instance_projects/devops-yucelsan-site root@$SCW_IP:/opt/scw_instance_projects/
scp -i "$SSH_KEY_PATH" -r /root/scw_instance_projects/environment-nginx root@$SCW_IP:/opt/scw_instance_projects/

echo "Connexion SSH to instance Scaleway and installation Nginx && Docker Compose ..."
ssh -i "$SSH_KEY_PATH" root@$SCW_IP << EOF
cp /opt/scw_instance_projects/environment-nginx/devops.yucelsan.fr /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/devops.yucelsan.fr /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
certbot --nginx -d devops.yucelsan.fr --non-interactive --agree-tos --redirect --email contact@yucelsan.fr
cd /opt/scw_instance_projects/yucelsan-devops-test && docker compose up -d
EOF

if [ $? -ne 0 ]; then
  echo "ERREUR lors de la copie des dossiers."
  exit 1
fi

if [ $? -eq 0 ]; then
  echo "Déploiement terminé avec succès."
else
  echo "ERREUR lors du déploiement Docker."
  exit 1
fi
