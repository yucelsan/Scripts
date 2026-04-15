#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/core/config.py     
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

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "INFRA ROCKET 6")
    APP_ENV = os.getenv("APP_ENV", "PROD")
    SECRET_KEY = os.getenv("SECRET_KEY", "ITSALONGPASSPHRASESECRETKEYINFRAROCKET6")

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "infraR_db")
    DB_USER = os.getenv("DB_USER", "infraR_admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "**********")

    LDAP_SERVER = os.getenv("LDAP_SERVER", "infraRocket.r6.local")
    LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "DC=r6,DC=local")
    LDAP_DOMAIN = os.getenv("LDAP_DOMAIN", "r6.local")
    ZABBIX_URL = os.getenv("ZABBIX_URL", "https://r6-zbx-v11.r6.local/api_jsonrpc.php")
    ZABBIX_API_TOKEN = os.getenv("ZABBIX_API_TOKEN")
    ZABBIX_VERIFY_SSL = os.getenv("ZABBIX_VERIFY_SSL", "true").lower() == "true"


settings = Settings()
