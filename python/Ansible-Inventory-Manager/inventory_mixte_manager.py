#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
#
# Projet      : ANSIBLE INVENTORY MANAGER
# Fichier     : inventory_mixte_manager.py
# Description : Ce script génère un fichier d'inventaire Windows & Linux hosts-mixte.yml (YAML) prêt à être utilisé par les playbooks.
# Auteur      : Serdar AYSAN
# Contact     : contact@yucelsan.fr
# Créé le     : 2025-10-28
# Version     : 0.2.0

import json
import yaml
class DoubleQuoted(str): pass

class Server:
    def __init__(self, hostname, ip, role, environment, extras=None):
        self.hostname = hostname
        self.ip = ip
        self.role = role
        self.environment = environment
        self.extras = extras or {}

    def __repr__(self):
        return f"Server(hostname={self.hostname}, ip={self.ip}, role={self.role}, environment={self.environment})"

    def to_ansible_dict(self):
        base = {
            "ansible_host": self.ip,
            "role": self.role,  # Ajouter le rôle ici
            "environment": self.environment,  # Ajouter l'environnement ici
        }
        base.update(self.extras)
        return { self.hostname: base }


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
        return {
            self.name: {
                "hosts": {
                    server.hostname: server.to_ansible_dict()[server.hostname]
                    for server in self.servers
                }
            }
        }


def represent_double_quoted(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(DoubleQuoted, represent_double_quoted)


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
        return "\n".join(str(server) for server in servers)

    def save_to_file(self, filename):
        inventory_dict = { "all": { "children": {} } }
        for _, group in self.groups.items():
            inventory_dict["all"]["children"].update(group.to_ansible_group())
        # Sauvegarder l'inventaire dans un fichier YAML
        with open(filename, "w") as file:
            yaml.dump(inventory_dict, file, default_flow_style=False, sort_keys=False, allow_unicode=True, width=4096)
#            yaml.dump(inventory_dict, file, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def load_from_file(self, filename):
        with open(filename, "r") as file:
            inventory_dict = yaml.safe_load(file) or {}
        all_node = inventory_dict.get("all") or {}
        children = all_node.get("children") or {}

        for group_name, group_data in children.items():
            group = ServerGroup(group_name)
            hosts = (group_data or {}).get("hosts") or {}
            for server_name, server_data in hosts.items():
                server = Server(
                    hostname=server_name,
                    ip=server_data["ansible_host"],
                    role=server_data.get("role", "linux"),
                    environment=server_data.get("environment", "production"),
                )
                group.add_server(server)
            self.add_group(group)


inventory = Inventory()

# Créer un groupe pour les serveurs
group_linux = ServerGroup("LinuxServers")
group_windows = ServerGroup('WindowsServers')

# Extras communs Linux: user, clé, python
linux_extras = {
    "ansible_user": "root",
    "ansible_ssh_private_key_file": "/root/.ssh/ansiblekey",
    "ansible_python_interpreter": "/usr/bin/python3",
}

# --- Windows hosts
win_user = DoubleQuoted(r"YSLN\SRVpolat")  # le backslash est échappé proprement
win_pass_lookup = DoubleQuoted("{{ lookup('file', '/ansible/.env/.vault/secret.yml') }}")

# Extras communs Windows (spécifiques par hôte pour user/pass)
winrm_common = {
    "ansible_connection": "winrm",
    "ansible_winrm_transport": "ntlm",
    "ansible_winrm_server_cert_validation": "ignore",
    "ansible_port": 5985,
}

group_linux.add_server(Server("VM-WEB-V01", "192.168.0.71", "linux", "production", extras=linux_extras))
group_linux.add_server(Server("VM-BDD-V02", "192.168.0.72", "linux", "production", extras=linux_extras))
group_linux.add_server(Server("VM-ORA-V03", "192.168.0.73", "linux", "production", extras=linux_extras))
group_linux.add_server(Server("VM-ANS-V04", "192.168.0.74", "linux", "production", extras=linux_extras))
group_linux.add_server(Server("VM-NET-V05", "192.168.0.75", "linux", "production", extras=linux_extras))
group_linux.add_server(Server("VM-ZBX-V06", "192.168.0.76", "linux", "production", extras=linux_extras))

group_windows.add_server(Server(
    "VM-WORKFLOW-DEV", "192.168.17.1", "windows", "developpement",
    extras = dict(winrm_common, **{
        "ansible_user": win_user,
        "ansible_password": win_pass_lookup,
    })
))
group_windows.add_server(Server(
    "VM-WORKFLOW-PRD", "192.168.17.2", "windows", "production",
    extras = dict(winrm_common, **{
        "ansible_user": win_user,
        "ansible_password": win_pass_lookup,
    })
))

inventory.add_group(group_linux)
inventory.add_group(group_windows)

# Sauvegarder l'inventaire
inventory.save_to_file("hosts-mixte.yml")


# Charger l'inventaire à partir d'un fichier
new_inventory = Inventory()
new_inventory.load_from_file("hosts-mixte.yml")
print(new_inventory.get_all_servers())
