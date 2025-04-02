#!/bin/bash

# Create project structure for devops-platform

mkdir -p frontend/public
mkdir -p frontend/src/{components,pages,styles,utils}
touch frontend/.env.example frontend/package.json

mkdir -p backend/app/{api,core,models,services}
mkdir -p backend/tests
touch backend/app/main.py backend/requirements.txt backend/.env.example

mkdir -p infrastructure/ansible/{inventories/dev,inventories/prod,roles,playbooks}
mkdir -p infrastructure/terraform/aws
mkdir -p infrastructure/bash-scripts
mkdir -p infrastructure/python-scripts
touch infrastructure/ansible/playbooks/deploy_env.yml
touch infrastructure/ansible/ansible.cfg
touch infrastructure/bash-scripts/init.sh
touch infrastructure/python-scripts/launcher.py
touch infrastructure/terraform/variables.tf

mkdir -p config/{nginx,systemd,gunicorn}

mkdir -p docs
touch docs/{architecture.md,roadmap.md,api-specs.md}

mkdir -p deployments/docker
mkdir -p deployments/github-actions
touch deployments/docker/{frontend.Dockerfile,backend.Dockerfile}
touch deployments/github-actions/ci.yml

touch README.md LICENSE .gitignore

echo 'Structure du projet créée avec succès !'
