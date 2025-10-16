#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Projet      : ANSIBLE INVENTORY MANAGER
# Fichier     : inventory_manager.py
# Description : Ce script génère un fichier d'inventaire hosts.yml (YAML) prêt à être utilisé par les playbooks.
# Auteur      : Serdar AYSAN
# Contact     : contact@yucelsan.fr
# Créé le     : 2025-10-17
# Version     : 0.1.0

import yaml

class Server:
    def __init__(self, hostname, ip, role, environment):
        self.hostname = hostname
        self.ip = ip
        self.role = role
        self.environment = environment

    def __repr__(self):
        return f"Server(hostname={self.hostname}, ip={self.ip}, role={self.role}, environment={self.environment})"

    def to_ansible_dict(self):
        return {
            self.hostname: {
                'ansible_host': self.ip,
                'ansible_python_interpreter': '/usr/bin/python3',  # Ajuster en fonction du système
                'role': self.role,  # Ajouter le rôle ici
                'environment': self.environment  # Ajouter l'environnement ici
            }
        }


class ServerGroup:
    def __init__(self, name):
        self.name = name
        self.servers = []

    def add_server(self, server):
        self.servers.append(server)

    def remove_server(self, server):
        self.servers.remove(server)

    def __repr__(self):
        return f"ServerGroup({self.name}, Servers: {len(self.servers)})"

    def to_ansible_group(self):
        return {self.name: {'hosts': {server.hostname: server.to_ansible_dict()[server.hostname] for server in self.servers}}}


class Inventory:
    def __init__(self):
        self.groups = {}

    def add_group(self, group):
        self.groups[group.name] = group

    def remove_group(self, group_name):
        if group_name in self.groups:
            del self.groups[group_name]

    def get_all_servers(self):
        servers = []
        for group in self.groups.values():
            servers.extend(group.servers)
        return '\n'.join(str(server) for server in servers)

    def save_to_file(self, filename):
        inventory_dict = {
            'all': {
                'vars': {
                    'ansible_user': 'root',
                    'ansible_ssh_private_key_file': '/root/.ssh/ansiblekey'
                },
                'children': {}
            }
        }

        # Ajouter les groupes d'enfants sous "children"
        for group_name, group in self.groups.items():
            inventory_dict['all']['children'].update(group.to_ansible_group())

        # Sauvegarder l'inventaire dans un fichier YAML
        with open(filename, 'w') as file:
            yaml.dump(inventory_dict, file, default_flow_style=False, sort_keys=False)

    def load_from_file(self, filename):
        with open(filename, 'r') as file:
            inventory_dict = yaml.load(file, Loader=yaml.FullLoader)

            # Si la structure du fichier est correcte, on peut charger les groupes et les serveurs.
            for group_name, group_data in inventory_dict['all']['children'].items():
                group = ServerGroup(group_name)
                for server_name, server_data in group_data['hosts'].items():
                    # Crée un dictionnaire avec les données nécessaires pour chaque serveur
                    server = Server(
                        hostname=server_name,
                        ip=server_data['ansible_host'],
                        role=server_data.get('role', 'linux'),  # Valeur par défaut pour 'role'
                        environment=server_data.get('environment', 'production')  # Valeur par défaut pour 'environment'
                    )
                    group.add_server(server)
                    self.add_group(group)


inventory = Inventory()

# Créer un groupe pour les serveurs
group_linux = ServerGroup('LinuxServers')
# group_windows = ServerGroup('WindowsServers')

server1 = Server('VM-WEB-V01', '192.168.0.71', 'linux', 'production')
server2 = Server('VM-BDD-V02', '192.168.0.72', 'linux', 'production')
server3 = Server('VM-ORA-V03', '192.168.0.73', 'linux', 'production')
server4 = Server('VM-ANS-V04', '192.168.0.74', 'linux', 'production')
server5 = Server('VM-NET-V05', '192.168.0.75', 'linux', 'production')
server6 = Server('VM-ZBX-V06', '192.168.0.76', 'linux', 'production')
# server7 = Server('VM-WORKFLOW-DEV', '192.168.17.1', 'windows', 'developpement')
# server8 = Server('VM-WORKFLOW-PRD', '192.168.17.2', 'windows', 'production')

group_linux.add_server(server1)
group_linux.add_server(server2)
group_linux.add_server(server3)
group_linux.add_server(server4)
group_linux.add_server(server5)
group_linux.add_server(server6)
# group_windows.add_server(server7)
# group_windows.add_server(server8)

inventory.add_group(group_linux)
# inventory.add_group(group_windows)

# Sauvegarder l'inventaire
inventory.save_to_file('hosts.yml')

# Charger l'inventaire à partir d'un fichier
new_inventory = Inventory()
new_inventory.load_from_file('hosts.yml')
print(new_inventory.get_all_servers())
