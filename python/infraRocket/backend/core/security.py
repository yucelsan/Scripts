#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/core/security.py     
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

from itsdangerous import URLSafeSerializer
from backend.core.config import settings

serializer = URLSafeSerializer(settings.SECRET_KEY, salt="infraR-session")


def create_session_token(data: dict) -> str:
    return serializer.dumps(data)


def read_session_token(token: str):
    try:
        return serializer.loads(token)
    except Exception:
        return None
