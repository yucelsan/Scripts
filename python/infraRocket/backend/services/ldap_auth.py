#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/services/ldap_auth.py     
║ 🧑 Author        : Serdar AYSAN                   
║ 🌐 Website       : https://www.yucelsan.fr         
║ 📧 Contact       : contact@yucelsan.fr             
║ ⚙️ Version       : 1.0.0                         
║ 📦 Dependencies  : <requests, fastapi, etc.>       
║ 🖥️ Environment   : Linux / Docker / Kubernetes   
╠════════════════════════════════════════════════════
║ 🚀 Usage:                                                 
║     /opt/infraRocket/venv/bin/python -m uvicorn /   
║      backend.main:app --host 0.0.0.0 --port 8001            
╠════════════════════════════════════════════════════
║ 🔐 License: MIT / Private / YUCELSAN             
╚════════════════════════════════════════════════════
"""

from ldap3 import Server, Connection, ALL


class LDAPAuthenticationError(Exception):
    pass


class LDAPAuthenticator:
    def __init__(self, ldap_server: str, domain_suffix: str):
        self.ldap_server = ldap_server
        self.domain_suffix = domain_suffix

    def authenticate(self, login: str, password: str) -> bool:
        if not login or not password:
            raise LDAPAuthenticationError("Login et mot de passe requis.")

        user = f"{login}{self.domain_suffix}"

        try:
            server = Server(self.ldap_server, get_info=ALL)
            conn = Connection(server, user=user, password=password, auto_bind=True)
            conn.unbind()
            return True

        except Exception as e:
            error_message = str(e)
            raise LDAPAuthenticationError(self.parse_ldap_error(error_message))

    def parse_ldap_error(self, error: str) -> str:
        error_lower = error.lower()

        ldap_codes = {
            "525": "Utilisateur introuvable.",
            "52e": "Login ou mot de passe incorrect.",
            "530": "Non autorisé à se connecter à ce moment.",
            "531": "Non autorisé à se connecter à cet ordinateur.",
            "532": "Mot de passe expiré.",
            "533": "Compte désactivé.",
            "701": "Compte expiré.",
            "773": "Mot de passe requis.",
            "775": "Compte verrouillé.",
        }

        for code, message in ldap_codes.items():
            if code in error_lower:
                return message

        return f"Échec de l’authentification LDAP : {error}"

