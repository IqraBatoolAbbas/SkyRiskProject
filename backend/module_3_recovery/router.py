"""
Module 3 API Router: Recovery Route & Impact Analysis
Endpoints for multi-route generation, comparative analytics, and human operational approval.
"""

from datetime import datetime, timezone
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from db.connection import get_db
from db.models import Flight, TrajectoryPoint, RecoveryPlan, OperationalFlightPlan, AuditEvent, User
from module_3_recovery.recovery_generator import generate_recovery_routes

router = APIRouter(prefix="/api/recovery", tags=["Module 3: Recovery Route Decision Support"])

class ApprovalRequest(BaseModel):
    recovery_plan_id: str = Field(..., example="REC-PK781-ROUTED")
    approved_by: str = Field("Ayesha Rahman", example="Ayesha Rahman")
    approved_role: str = Field("flight_dispatcher", example="flight_dispatcher")
    notes: Optional[str] = Field("Approved after verifying safe separation and 82.8% risk reduction.", example="Approved after verifying safe separation.")

class RejectionRequest(BaseModel):
    recovery_plan_id: str = Field(..., example="REC-PK781-ROUTEA")
    rejected_by: str = Field("Ayesha Rahman", example="Ayesha Rahman")
    rejected_role: str = Field("flight_dispatcher", example="flight_dispatcher")
    reason: str = Field(..., example="Lateral detour passes too close to military TFR corridor.")

def compute_hash(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

@router.get("/summary")
def get_recovery_overview(db: Session = Depends(get_db)):
    """Summary metrics of all recovery route evaluations across monitored airspace."""
    flights_needing_recovery = db.query(Flight).filter(Flight.overall_risk_score >= 35.0).count()
    total_candidates = db.query(RecoveryPlan).count()
    approved_plans = db.query(RecoveryPlan).filter(RecoveryPlan.status == "APPROVED").count()

    plans = db.query(RecoveryPlan).all()
    evaluation_list = []
    for p in plans[:8]:
        evaluation_list.append({
            "candidate_id": p.id,
            "flight_id": p.flight_id,
            "strategy": p.strategy_name,
            "distance_change_km": p.distance_change_km,
            "delay_minutes": p.delay_minutes,
            "fuel_delta_kg": p.fuel_delta_kg,
            "risk_reduction_percent": p.risk_reduction_percent,
            "status": p.status,
            "is_operationally_approved": (p.status == "APPROVED"),
        })

    return {
        "status": "success",
        "project": "SkyRisk Auditor",
        "flight_assessment_count": db.query(Flight).count(),
        "flights_needing_recovery": flights_needing_recovery,
        "total_recovery_candidates": total_candidates,
        "approved_recoveries": approved_plans,
        "recovery_candidate_evaluation": evaluation_list,
        "interpretation": "Decision-support recovery candidate evaluations generated with 4D lateral/vertical trade-offs.",
    }

@router.get("/flights/{flight_id}")
def get_flight_recovery_plans(flight_id: str, db: Session = Depends(get_db)):
    """Retrieve candidate recovery options for a specific flight, generating candidates if needed."""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight '{flight_id}' not found.")

    plans = db.query(RecoveryPlan).filter(RecoveryPlan.flight_id == flight_id).all()
    if not plans:
        # Generate them
        generate_recovery_routes(flight_id, db)
        plans = db.query(RecoveryPlan).filter(RecoveryPlan.flight_id == flight_id).all()

    candidates = [
        {
            "id": p.id,
            "flight_id": p.flight_id,
            "candidate_code": p.candidate_code,
            "strategy_name": p.strategy_name,
            "route_description": p.route_description,
            "waypoints": p.waypoints_json,
            "distance_change_km": p.distance_change_km,
            "delay_minutes": p.delay_minutes,
            "fuel_delta_kg": p.fuel_delta_kg,
            "fuel_delta_percent": p.fuel_delta_percent,
            "original_risk_score": p.original_risk_score,
            "residual_risk_score": p.residual_risk_score,
            "risk_reduction_percent": p.risk_reduction_percent,
            "status": p.status,
            "approved_by": p.approved_by,
            "approved_at": p.approved_at.isoformat() if p.approved_at else None,
            "approval_notes": p.approval_notes,
            "is_operationally_approved": (p.status == "APPROVED"),
        }
        for p in plans
    ]

    return {
        "status": "success",
        "flight_id": flight_id,
        "call_sign": flight.call_sign,
        "current_flight_status": flight.status,
        "current_risk_score": round(flight.overall_risk_score, 1),
        "current_risk_band": flight.overall_risk_band,
        "active_recovery_id": flight.active_recovery_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }

@router.post("/generate/{flight_id}")
def trigger_recovery_generation(flight_id: str, db: Session = Depends(get_db)):
    """Trigger the multi-route generation algorithms for a flight."""
    try:
        candidates = generate_recovery_routes(flight_id, db)
        return {
            "status": "success",
            "message": f"Generated {len(candidates)} multi-route recovery options for flight '{flight_id}'.",
            "candidates": candidates,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/approve")
def approve_recovery_route(req: ApprovalRequest, db: Session = Depends(get_db)):
    """
    Authorized User approves a recovery route.
    Updates the flight trajectory, generates an Updated OFP, and writes an immutable audit record.
    """
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == req.recovery_plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found.")

    flight = db.query(Flight).filter(Flight.id == plan.flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Associated flight not found.")

    # Check RBAC authorization
    allowed_roles = ["flight_dispatcher", "safety_analyst", "admin"]
    if req.approved_role.lower() not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{req.approved_role}' is not authorized to approve operational recovery routes. Required: Flight Dispatcher or Safety Analyst."
        )

    now = datetime.now(timezone.utc)
    prev_state = {
        "status": flight.status,
        "risk_score": flight.overall_risk_score,
        "active_recovery_id": flight.active_recovery_id,
    }

    # 1. Update Plan Status
    plan.status = "APPROVED"
    plan.approved_by = req.approved_by
    plan.approved_role = req.approved_role
    plan.approved_at = now
    plan.approval_notes = req.notes

    # 2. Update Flight Status & 4D Waypoints
    flight.status = "Cleared (Recovered)"
    flight.overall_risk_score = plan.residual_risk_score
    flight.overall_risk_band = "LOW" if plan.residual_risk_score < 35.0 else "ELEVATED"
    flight.active_recovery_id = plan.id

    # Replace flight waypoints with approved recovery route waypoints
    if plan.waypoints_json:
        # Delete old waypoints
        db.query(TrajectoryPoint).filter(TrajectoryPoint.flight_id == flight.id).delete()
        for i, wp in enumerate(plan.waypoints_json):
            new_wp = TrajectoryPoint(
                flight_id=flight.id,
                sequence=i + 1,
                waypoint_name=wp.get("name", f"WPT-{i+1}"),
                latitude=wp["lat"],
                longitude=wp["lon"],
                altitude_ft=wp.get("alt", flight.cruise_altitude_ft),
                time_offset_min=int(wp.get("time_min", i * 20)),
                speed_kts=wp.get("speed_kts", 450.0),
                heading_deg=wp.get("heading_deg", 40.0),
                is_hotspot=False,
                hazard_score=round(plan.residual_risk_score * 0.4, 1),
            )
            db.add(new_wp)

    # 3. Generate Updated Operational Flight Plan (OFP)
    ofp_id = f"OFP-{flight.id}-REV{int(now.timestamp()) % 1000}"
    route_text = " DCT ".join(wp.get("name", "") for wp in (plan.waypoints_json or []))
    new_ofp = OperationalFlightPlan(
        id=ofp_id,
        flight_id=flight.id,
        recovery_plan_id=plan.id,
        version=2,
        status="APPROVED_RELEASE",
        dispatch_notes=f"Re-cleared on recovery route {plan.strategy_name}. Notes: {req.notes}",
        route_text=route_text or flight.route_string,
        cruise_fl=f"FL{flight.cruise_altitude_ft // 100}",
        block_fuel_kg=round(9200.0 + plan.fuel_delta_kg, 1),
        trip_fuel_kg=round(6800.0 + plan.fuel_delta_kg, 1),
        contingency_fuel_kg=350.0,
        alternate_fuel_kg=1150.0,
        reserve_fuel_kg=900.0,
        estimated_time_enroute_min=int(110 + plan.delay_minutes),
        dispatcher_signature=f"{req.approved_by} ({req.approved_role})",
        signed_at=now,
        navlog_data={"waypoints": plan.waypoints_json},
    )
    db.add(new_ofp)

    # 4. Write Immutable Audit Trail Event
    new_state = {
        "status": flight.status,
        "risk_score": flight.overall_risk_score,
        "approved_plan": plan.id,
        "ofp_id": ofp_id,
    }
    event_payload = {
        "actor": req.approved_by,
        "role": req.approved_role,
        "action": "ROUTE_APPROVED",
        "flight_id": flight.id,
        "plan_id": plan.id,
        "timestamp": now.isoformat(),
        "prev_state": prev_state,
        "new_state": new_state,
    }
    audit_event = AuditEvent(
        event_id=f"AUD-{int(now.timestamp() * 1000)}",
        timestamp=now,
        actor_name=req.approved_by,
        actor_role=req.approved_role,
        action="ROUTE_APPROVED",
        entity_type="RECOVERY",
        entity_id=plan.id,
        previous_state=prev_state,
        new_state=new_state,
        details=f"Approved recovery candidate '{plan.strategy_name}' for flight {flight.call_sign}. Residual risk reduced to {plan.residual_risk_score}/100. Generated updated OFP {ofp_id}.",
        payload_hash=compute_hash(event_payload),
    )
    db.add(audit_event)

    db.commit()

    return {
        "status": "success",
        "message": f"Recovery route '{plan.strategy_name}' approved successfully.",
        "flight_id": flight.id,
        "recovery_plan_id": plan.id,
        "ofp_id": ofp_id,
        "audit_event_id": audit_event.event_id,
        "new_risk_score": flight.overall_risk_score,
        "new_status": flight.status,
    }

@router.post("/reject")
def reject_recovery_route(req: RejectionRequest, db: Session = Depends(get_db)):
    """Reject a recovery candidate route and record operational reasoning in audit log."""
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == req.recovery_plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found.")

    plan.status = "REJECTED"
    plan.approved_by = req.rejected_by
    plan.approved_role = req.rejected_role
    plan.approval_notes = f"REJECTED: {req.reason}"

    now = datetime.now(timezone.utc)
    audit = AuditEvent(
        event_id=f"AUD-{int(now.timestamp() * 1000)}",
        timestamp=now,
        actor_name=req.rejected_by,
        actor_role=req.rejected_role,
        action="ROUTE_REJECTED",
        entity_type="RECOVERY",
        entity_id=plan.id,
        details=f"Rejected recovery plan '{plan.strategy_name}' for flight {plan.flight_id}. Reason: {req.reason}",
        payload_hash=compute_hash({"action": "ROUTE_REJECTED", "plan": plan.id, "reason": req.reason}),
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Recovery route '{plan.strategy_name}' marked REJECTED.",
        "plan_id": plan.id,
    }
