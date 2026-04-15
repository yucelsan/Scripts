#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/services/user_service.py     
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

from datetime import datetime
from backend.db.database import SessionLocal
from backend.db.models import InfraRUser


def _user_to_dict(user: InfraRUser) -> dict:
    return {
        "login": user.login,
        "prenom": user.prenom or "",
        "nom": user.nom or "",
        "full_name": f"{user.prenom or ''} {user.nom or ''}".strip(),
        "email": user.email or "",
        "service": user.service or "",
        "role": user.role,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.strftime("%d/%m/%Y %H:%M") if user.last_login_at else None,
        "created_at": user.created_at.strftime("%d/%m/%Y") if user.created_at else None,
    }


class UserService:

    @staticmethod
    def get_user_by_login(login: str):
        db = SessionLocal()
        try:
            user = db.query(InfraRUser).filter(InfraRUser.login == login).first()
            if not user:
                return None
            return _user_to_dict(user)
        finally:
            db.close()

    @staticmethod
    def get_all_users():
        db = SessionLocal()
        try:
            users = db.query(InfraRUser).order_by(InfraRUser.login).all()
            return [_user_to_dict(u) for u in users]
        finally:
            db.close()

    @staticmethod
    def create_user(login: str, prenom: str = "", nom: str = "", email: str = "",
                    service: str = "", role: str = "user", is_active: bool = True):
        db = SessionLocal()
        try:
            user = InfraRUser(
                login=login,
                prenom=prenom or None,
                nom=nom or None,
                email=email or None,
                service=service or None,
                role=role,
                is_active=is_active,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return _user_to_dict(user)
        finally:
            db.close()

    @staticmethod
    def update_user(login: str, prenom: str = "", nom: str = "", email: str = "",
                    service: str = "", role: str = "user", is_active: bool = True):
        db = SessionLocal()
        try:
            user = db.query(InfraRUser).filter(InfraRUser.login == login).first()
            if not user:
                return None
            user.prenom = prenom or None
            user.nom = nom or None
            user.email = email or None
            user.service = service or None
            user.role = role
            user.is_active = is_active
            db.commit()
            db.refresh(user)
            return _user_to_dict(user)
        finally:
            db.close()

    @staticmethod
    def delete_user(login: str) -> bool:
        db = SessionLocal()
        try:
            user = db.query(InfraRUser).filter(InfraRUser.login == login).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def update_last_login(login: str):
        db = SessionLocal()
        try:
            user = db.query(InfraRUser).filter(InfraRUser.login == login).first()
            if user:
                user.last_login_at = datetime.now()
                db.commit()
        finally:
            db.close()

