"""
Module 1 API Router: Flight & 4D Trajectory Management
Provides REST endpoints for flight plan submission, 4D trajectory retrieval,
telemetry stream tracking, and active airspace flights.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from db.connection import get_db
from db.models import Flight, TrajectoryPoint
from module_1_trajectory.trajectory_service import generate_4d_trajectory, AERODROMES

router = APIRouter(prefix="/api/flights", tags=["Module 1: 4D Trajectory Management"])

class FlightPlanCreate(BaseModel):
    call_sign: str = Field(..., min_length=2, max_length=15, example="PK-781")
    aircraft_type: str = Field("A320-200", example="A320-200")
    origin: str = Field(..., min_length=4, max_length=4, example="OPKC")
    destination: str = Field(..., min_length=4, max_length=4, example="OPLA")
    alternate_airport: Optional[str] = Field("OPIS", example="OPIS")
    cruise_altitude_ft: int = Field(36000, ge=5000, le=50000, example=36000)
    cruise_speed_kts: int = Field(450, ge=120, le=600, example=450)
    route_string: Optional[str] = Field(None, example="OPKC DCT RK J121 SULOM J130 OPLA")

@router.get("/")
def list_flights(db: Session = Depends(get_db)):
    """Retrieve all flights registered in the 4D monitoring airspace."""
    flights = db.query(Flight).order_by(Flight.created_at.desc()).all()
    results = []
    for f in flights:
        wpt_count = len(f.waypoints)
        results.append({
            "id": f.id,
            "call_sign": f.call_sign,
            "aircraft_type": f.aircraft_type,
            "origin": f.origin,
            "origin_name": f.origin_name,
            "destination": f.destination,
            "destination_name": f.destination_name,
            "alternate_airport": f.alternate_airport,
            "cruise_altitude_ft": f.cruise_altitude_ft,
            "cruise_speed_kts": f.cruise_speed_kts,
            "route_string": f.route_string,
            "status": f.status,
            "phase": f.phase,
            "overall_risk_score": round(f.overall_risk_score, 1),
            "overall_risk_band": f.overall_risk_band,
            "monitoring_active": f.monitoring_active,
            "waypoint_count": wpt_count,
            "departure_utc": f.planned_departure_utc.isoformat() if f.planned_departure_utc else None,
            "estimated_arrival_utc": f.estimated_arrival_utc.isoformat() if f.estimated_arrival_utc else None,
        })
    return {"status": "success", "count": len(results), "flights": results}

@router.get("/aerodromes")
def list_aerodromes():
    """List available origin and destination aerodromes with 3D geographic coordinates."""
    return {"status": "success", "aerodromes": AERODROMES}

@router.get("/{flight_id}")
def get_flight_trajectory(flight_id: str, db: Session = Depends(get_db)):
    """Retrieve complete 4D trajectory (lat, lon, altitude, time, speed, heading) for a specific flight."""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight '{flight_id}' not found.")

    waypoints = [
        {
            "sequence": wp.sequence,
            "name": wp.waypoint_name,
            "lat": wp.latitude,
            "lon": wp.longitude,
            "alt": wp.altitude_ft,
            "time_min": wp.time_offset_min,
            "speed_kts": wp.speed_kts,
            "heading_deg": wp.heading_deg,
            "is_hotspot": wp.is_hotspot,
            "hazard_score": wp.hazard_score,
            "weather_hazard": wp.weather_hazard,
            "space_weather_kp": wp.space_weather_kp,
            "notam_conflict": wp.notam_conflict,
        }
        for wp in flight.waypoints
    ]

    return {
        "status": "success",
        "flight": {
            "id": flight.id,
            "call_sign": flight.call_sign,
            "aircraft_type": flight.aircraft_type,
            "origin": flight.origin,
            "origin_name": flight.origin_name,
            "destination": flight.destination,
            "destination_name": flight.destination_name,
            "alternate_airport": flight.alternate_airport,
            "cruise_altitude_ft": flight.cruise_altitude_ft,
            "cruise_speed_kts": flight.cruise_speed_kts,
            "route_string": flight.route_string,
            "status": flight.status,
            "phase": flight.phase,
            "overall_risk_score": round(flight.overall_risk_score, 1),
            "overall_risk_band": flight.overall_risk_band,
            "active_recovery_id": flight.active_recovery_id,
            "waypoints": waypoints,
        }
    }

@router.post("/")
def create_flight_plan(payload: FlightPlanCreate, db: Session = Depends(get_db)):
    """Submit a new flight plan and automatically generate its 4D trajectory representation."""
    flight_id = f"{payload.call_sign.upper()}-{payload.origin.upper()}{payload.destination.upper()}"

    # Check if duplicate
    existing = db.query(Flight).filter(Flight.id == flight_id).first()
    if existing:
        flight_id = f"{payload.call_sign.upper()}-{int(datetime.now().timestamp()) % 10000}"

    origin_info = AERODROMES.get(payload.origin.upper(), {"name": f"{payload.origin.upper()} Aerodrome"})
    dest_info = AERODROMES.get(payload.destination.upper(), {"name": f"{payload.destination.upper()} Aerodrome"})

    # Compute 4D trajectory points
    traj = generate_4d_trajectory(
        origin_icao=payload.origin.upper(),
        dest_icao=payload.destination.upper(),
        cruise_fl=payload.cruise_altitude_ft // 100,
        cruise_speed_kts=payload.cruise_speed_kts,
    )

    flight = Flight(
        id=flight_id,
        call_sign=payload.call_sign.upper(),
        aircraft_type=payload.aircraft_type,
        origin=payload.origin.upper(),
        origin_name=origin_info.get("name"),
        destination=payload.destination.upper(),
        destination_name=dest_info.get("name"),
        alternate_airport=payload.alternate_airport.upper() if payload.alternate_airport else "OPIS",
        cruise_altitude_ft=payload.cruise_altitude_ft,
        cruise_speed_kts=payload.cruise_speed_kts,
        route_string=payload.route_string or f"{payload.origin.upper()} DCT {payload.destination.upper()}",
        status="Planned",
        phase="Pre-flight",
        overall_risk_score=0.0,
        overall_risk_band="LOW",
        monitoring_active=True,
    )
    db.add(flight)
    db.flush()

    # Save 4D waypoints
    for wp in traj["waypoints"]:
        db_wp = TrajectoryPoint(
            flight_id=flight.id,
            sequence=wp["sequence"],
            waypoint_name=wp["name"],
            latitude=wp["lat"],
            longitude=wp["lon"],
            altitude_ft=wp["alt"],
            time_offset_min=int(wp["time_min"]),
            speed_kts=wp["speed_kts"],
            heading_deg=wp["heading_deg"],
            is_hotspot=False,
            hazard_score=0.0,
        )
        db.add(db_wp)

    db.commit()
    db.refresh(flight)

    return {
        "status": "success",
        "message": f"Flight '{flight.call_sign}' 4D trajectory generated successfully.",
        "flight_id": flight.id,
        "waypoint_count": len(traj["waypoints"]),
        "total_distance_km": traj["total_distance_km"],
        "total_time_min": traj["total_time_enroute_min"],
    }
