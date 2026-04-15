#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/routers/dashboard.py     
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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from backend.core.security import read_session_token
from backend.services.zabbix_service import ZabbixService

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")


def get_session_or_redirect(request: Request):
    token = request.cookies.get("infraR_session")
    if not token:
        return None

    session_data = read_session_token(token)
    if not session_data:
        return None

    return session_data


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    session_data = get_session_or_redirect(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    zabbix_data = {
        "critical_alerts": 0,
        "down_hosts": 0,
        "last_sync": "Erreur Zabbix"
    }

    try:
        zabbix_service = ZabbixService()
        zabbix_data = zabbix_service.get_dashboard_summary()
    except Exception as e:
        print(f"Zabbix error: {e}")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "user": session_data,
            "zabbix": zabbix_data
        }
    )


@router.get("/topology", response_class=HTMLResponse)
def topology_page(request: Request):
    session_data = get_session_or_redirect(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        request,
        "topology.html",
        {
            "request": request,
            "user": session_data
        }
    )


@router.get("/api/topology", response_class=JSONResponse)
def topology_api(request: Request):
    session_data = get_session_or_redirect(request)
    if not session_data:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        zabbix_service = ZabbixService()
        data = zabbix_service.build_topology()
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse(
            {
                "error": "topology_build_failed",
                "details": str(e)
            },
            status_code=500
        )


@router.get("/api/topology/site/{site_slug}", response_class=JSONResponse)
def topology_site_api(request: Request, site_slug: str):
    session_data = get_session_or_redirect(request)
    if not session_data:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        zabbix_service = ZabbixService()
        data = zabbix_service.build_topology(site_filter=site_slug)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse(
            {
                "error": "topology_site_build_failed",
                "details": str(e)
            },
            status_code=500
        )

