"""
Module 2 API Router: Multi-Hazard Risk Assessment
Endpoints for airspace hazard monitoring, 4D risk evaluation, and NOTAM classification.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from db.connection import get_db
from db.models import Hazard, Flight
from module_2_risk_hazards.risk_service import evaluate_flight_risk
from module_2_risk_hazards.notam_nlp import classify_notam

router = APIRouter(prefix="/api/risk", tags=["Module 2: Multi-Hazard Risk Assessment"])

class NotamRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000, example="A0482/26 NOTAMN Q) OPKR/QMRLC/IV/NBO/A/000/999/3131N07424E005 A) OPLA B) 2610240800 C) 2610241600 E) RWY 36R/18L CLSD DUE WIP.")

class HazardCreate(BaseModel):
    id: str = Field(..., example="HAZ-WX-CUSTOM-01")
    hazard_type: str = Field("WEATHER", example="WEATHER")  # WEATHER, SPACE_WEATHER, NOTAM, AIRSPACE_CONFLICT
    title: str = Field(..., example="Severe Thunderstorm Cell")
    severity: str = Field("HIGH", example="HIGH")  # LOW, MEDIUM, HIGH, SEVERE
    center_latitude: float = Field(..., example=30.2)
    center_longitude: float = Field(..., example=71.4)
    radius_km: float = Field(50.0, example=60.0)
    min_altitude_ft: int = Field(10000, example=15000)
    max_altitude_ft: int = Field(45000, example=42000)
    description: str = Field(..., example="Convective storm tops at FL420.")

@router.get("/hazards")
def list_active_hazards(db: Session = Depends(get_db)):
    """Retrieve all active spatial and environmental hazards across the monitored FIR airspace."""
    hazards = db.query(Hazard).filter(Hazard.is_active == True).all()
    results = [
        {
            "id": h.id,
            "type": h.hazard_type,
            "title": h.title,
            "severity": h.severity,
            "lat": h.center_latitude,
            "lon": h.center_longitude,
            "radius_km": h.radius_km,
            "min_alt_ft": h.min_altitude_ft,
            "max_alt_ft": h.max_altitude_ft,
            "description": h.description,
            "raw_payload": h.raw_payload,
            "effective_start": h.effective_start.isoformat() if h.effective_start else None,
            "effective_end": h.effective_end.isoformat() if h.effective_end else None,
        }
        for h in hazards
    ]
    return {"status": "success", "count": len(results), "hazards": results}

@router.post("/hazards")
def create_hazard(payload: HazardCreate, db: Session = Depends(get_db)):
    """Inject a new operational hazard into the airspace for real-time risk assessment."""
    existing = db.query(Hazard).filter(Hazard.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Hazard ID '{payload.id}' already exists.")

    h = Hazard(
        id=payload.id,
        hazard_type=payload.hazard_type.upper(),
        title=payload.title,
        severity=payload.severity.upper(),
        center_latitude=payload.center_latitude,
        center_longitude=payload.center_longitude,
        radius_km=payload.radius_km,
        min_altitude_ft=payload.min_altitude_ft,
        max_altitude_ft=payload.max_altitude_ft,
        description=payload.description,
        is_active=True,
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    return {"status": "success", "message": f"Hazard '{h.id}' created and active in airspace."}

@router.get("/evaluate/{flight_id}")
def evaluate_risk(flight_id: str, db: Session = Depends(get_db)):
    """Evaluate 4D trajectory multi-hazard risk for a specific flight."""
    try:
        return evaluate_flight_risk(flight_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk evaluation error: {str(e)}")

@router.post("/notam/classify")
def classify_notam_text(req: NotamRequest):
    """Classify NOTAM text using DistilBERT NLP model with structured entity extraction."""
    result = classify_notam(req.text)
    return {"status": "success", **result}
