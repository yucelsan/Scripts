#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/routers/admin.py     
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

import logging

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.core.security import read_session_token
from backend.services.user_service import UserService

logger = logging.getLogger("infraR_api")
router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="backend/templates")


def get_admin_session(request: Request):
    """Vérifie que l'utilisateur est connecté ET admin."""
    token = request.cookies.get("infraR_session")
    if not token:
        return None
    session_data = read_session_token(token)
    if not session_data:
        return None
    if session_data.get("role") != "admin":
        return None
    return session_data


# ─── Liste des utilisateurs ───────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request):
    session_data = get_admin_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    users = UserService.get_all_users()
    return templates.TemplateResponse(
        request,
        "admin_users.html",
        {
            "request": request,
            "user": session_data,
            "users": users,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        }
    )


# ─── Formulaire ajout ─────────────────────────────────────────────────────────

@router.get("/users/add", response_class=HTMLResponse)
def admin_user_add_form(request: Request):
    session_data = get_admin_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        request,
        "admin_user_form.html",
        {
            "request": request,
            "user": session_data,
            "form_user": None,
            "action": "add",
            "error": None,
        }
    )


@router.post("/users/add", response_class=HTMLResponse)
def admin_user_add(
    request: Request,
    login: str = Form(...),
    prenom: str = Form(""),
    nom: str = Form(""),
    email: str = Form(""),
    service: str = Form(""),
    role: str = Form("user"),
    is_active: str = Form("on"),
):
    session_data = get_admin_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    login = login.strip().lower()
    role = role if role in ("admin", "user") else "user"
    active = is_active == "on"

    existing = UserService.get_user_by_login(login)
    if existing:
        return templates.TemplateResponse(
            request,
            "admin_user_form.html",
            {
                "request": request,
                "user": session_data,
                "form_user": {
                    "login": login,
                    "prenom": prenom,
                    "nom": nom,
                    "email": email,
                    "service": service,
                    "role": role,
                    "is_active": active,
                },
                "action": "add",
                "error": f'Le login "{login}" existe déjà.',
            }
        )

    UserService.create_user(
        login=login,
        prenom=prenom.strip(),
        nom=nom.strip(),
        email=email.strip(),
        service=service.strip(),
        role=role,
        is_active=active,
    )

    logger.info(f"[ADMIN] user_created login={login} by={session_data['login']}")
    return RedirectResponse(url="/admin/users?success=Utilisateur+créé+avec+succès", status_code=302)


# ─── Formulaire modification ──────────────────────────────────────────────────

@router.get("/users/edit/{login}", response_class=HTMLResponse)
def admin_user_edit_form(request: Request, login: str):
    session_data = get_admin_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    form_user = UserService.get_user_by_login(login)
    if not form_user:
        return RedirectResponse(url="/admin/users?error=Utilisateur+introuvable", status_code=302)

    return templates.TemplateResponse(
        request,
        "admin_user_form.html",
        {
            "request": request,
            "user": session_data,
            "form_user": form_user,
            "action": "edit",
            "error": None,
        }
    )


@router.post("/users/edit/{login}", response_class=HTMLResponse)
def admin_user_edit(
    request: Request,
    login: str,
    prenom: str = Form(""),
    nom: str = Form(""),
    email: str = Form(""),
    service: str = Form(""),
    role: str = Form("user"),
    is_active: str = Form(None),
):
    session_data = get_admin_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    role = role if role in ("admin", "user") else "user"
    active = is_active == "on"

    # Sécurité : un admin ne peut pas se désactiver ni se rétrograder lui-même
    if login == session_data["login"]:
        active = True
        role = "admin"

    updated = UserService.update_user(
        login=login,
        prenom=prenom.strip(),
        nom=nom.strip(),
        email=email.strip(),
        service=service.strip(),
        role=role,
        is_active=active,
    )

    if not updated:
        return RedirectResponse(url="/admin/users?error=Utilisateur+introuvable", status_code=302)

    logger.info(f"[ADMIN] user_updated login={login} by={session_data['login']}")
    return RedirectResponse(url="/admin/users?success=Utilisateur+modifié+avec+succès", status_code=302)


# ─── Suppression ──────────────────────────────────────────────────────────────

@router.post("/users/delete/{login}")
def admin_user_delete(request: Request, login: str):
    session_data = get_admin_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    # Sécurité : un admin ne peut pas se supprimer lui-même
    if login == session_data["login"]:
        return RedirectResponse(url="/admin/users?error=Vous+ne+pouvez+pas+supprimer+votre+propre+compte", status_code=302)

    deleted = UserService.delete_user(login)
    if not deleted:
        return RedirectResponse(url="/admin/users?error=Utilisateur+introuvable", status_code=302)

    logger.info(f"[ADMIN] user_deleted login={login} by={session_data['login']}")
    return RedirectResponse(url="/admin/users?success=Utilisateur+supprimé+avec+succès", status_code=302)
