#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/routers/auth.py     
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
import logging

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import create_session_token
from backend.db.database import get_db
from backend.services.ldap_auth import LDAPAuthenticator, LDAPAuthenticationError
from backend.services.user_service import UserService

logger = logging.getLogger("infraR_api")
router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="backend/templates")

ldap_authenticator = LDAPAuthenticator(
    ldap_server=settings.LDAP_SERVER,
    domain_suffix=f"@{settings.LDAP_DOMAIN}"
)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "error": None
        }
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    login_value = username.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    if not login_value or not password:
        logger.warning(f"[AUTH_FAIL] empty_credentials ip={client_ip}")
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": "Login et mot de passe requis."
            }
        )

    user = UserService.get_user_by_login(login_value)
    if not user:
        logger.warning(f"[AUTH_FAIL] user_not_found user={login_value} ip={client_ip}")
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": f'Identifiant "{login_value}" non trouvé dans la base.'
            }
        )

    if not user.get("is_active", False):
        logger.warning(f"[AUTH_FAIL] user_disabled user={login_value} ip={client_ip}")
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": "Compte désactivé."
            }
        )

    try:
        ldap_authenticator.authenticate(login_value, password)
    except LDAPAuthenticationError as e:
        logger.warning(f"[AUTH_FAIL] ldap_error user={login_value} ip={client_ip}")
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": str(e)
            }
        )

    UserService.update_last_login(login_value)

    logger.info(f"[AUTH_SUCCESS] user={login_value} ip={client_ip} agent={user_agent}")

    session_token = create_session_token({
        "login": user["login"],
        "role": user["role"],
        "full_name": user.get("full_name", "")
    })

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="infraR_session",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("infraR_session")
    return response

