#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/db/database.py     
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

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.core.config import settings

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=int(settings.DB_PORT),
    database=settings.DB_NAME,
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

