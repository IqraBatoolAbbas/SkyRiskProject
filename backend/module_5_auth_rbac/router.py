"""
Module 5 API Router: Authentication & Role-Based Access Control (RBAC)
Implements role authorizations for the 4 target operational profiles:
- Flight Dispatcher
- Aviation Safety Analyst
- Aviation Security Auditor
- Meteorological Analyst
"""

import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from db.connection import get_db
from db.models import User

router = APIRouter(prefix="/api/auth", tags=["Module 5: RBAC & Authentication"])

ROLE_CAPABILITIES = {
    "flight_dispatcher": {
        "title": "Flight Dispatcher",
        "description": "Responsible for flight planning, trajectory monitoring, recovery route generation, and final operational flight release approval.",
        "permissions": [
            "create_flight_plan",
            "trigger_recovery",
            "approve_recovery_route",
            "reject_recovery_route",
            "sign_ofp",
            "view_risk_dashboard",
        ],
        "can_approve_recovery": True,
        "can_sign_ofp": True,
        "can_edit_hazards": False,
    },
    "safety_analyst": {
        "title": "Aviation Safety Analyst",
        "description": "Analyzes 4D multi-hazard cascading risks, validates model reliability, inspects proxy indicators, and reviews safety clearances.",
        "permissions": [
            "view_risk_dashboard",
            "inspect_cascading_factors",
            "audit_risk_models",
            "approve_recovery_route",
            "flag_safety_violation",
        ],
        "can_approve_recovery": True,
        "can_sign_ofp": False,
        "can_edit_hazards": True,
    },
    "security_auditor": {
        "title": "Aviation Security Auditor",
        "description": "Maintains oversight on operational compliance, verifies cryptographic audit logs, inspects tamper-proof event chains.",
        "permissions": [
            "view_audit_trail",
            "verify_audit_integrity",
            "export_audit_records",
            "inspect_user_actions",
        ],
        "can_approve_recovery": False,
        "can_sign_ofp": False,
        "can_edit_hazards": False,
    },
    "met_analyst": {
        "title": "Meteorological Analyst",
        "description": "Monitors meteorological Doppler radar, NOAA SWPC space-weather solar flare alerts, and calibrates DistilBERT NOTAM classification.",
        "permissions": [
            "ingest_weather_feed",
            "calibrate_swpc_kp",
            "test_notam_distilbert",
            "create_hazard_alert",
            "view_risk_dashboard",
        ],
        "can_approve_recovery": False,
        "can_sign_ofp": False,
        "can_edit_hazards": True,
    },
}

class LoginRequest(BaseModel):
    username: str = Field(..., example="dispatcher_ayesha")
    password: str = Field(..., example="dispatch123")

class SwitchRoleRequest(BaseModel):
    role: str = Field(..., example="flight_dispatcher")

def hash_pw(pw: str) -> str:
    return hashlib.sha256(f"skyrisk_salt_{pw}".encode()).hexdigest()

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with username and password, returning user profile and RBAC permissions."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if user.password_hash != hash_pw(req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    role_info = ROLE_CAPABILITIES.get(user.role, {
        "title": user.role.title(),
        "description": "Operational user.",
        "permissions": ["view_risk_dashboard"],
        "can_approve_recovery": False,
    })

    return {
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "dispatcher_id": user.dispatcher_id,
            "role_capabilities": role_info,
        },
        "token": f"skyrisk_token_{user.username}_{int(datetime.now().timestamp())}",
    }

@router.get("/users")
def list_personnel(db: Session = Depends(get_db)):
    """List all authorized operational personnel and their system roles."""
    users = db.query(User).all()
    results = [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "role_title": ROLE_CAPABILITIES.get(u.role, {}).get("title", u.role),
            "dispatcher_id": u.dispatcher_id,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]
    return {
        "status": "success",
        "users": results,
        "available_roles": ROLE_CAPABILITIES,
    }

@router.get("/roles")
def get_roles():
    """Retrieve details and permission matrix for all supported aviation roles."""
    return {"status": "success", "roles": ROLE_CAPABILITIES}
