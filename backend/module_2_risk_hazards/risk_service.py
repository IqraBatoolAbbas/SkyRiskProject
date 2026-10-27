"""
Module 2: Multi-Hazard Risk Assessment Engine
Computes spatial-temporal risk along 4D flight trajectories.
Integrates Weather, Space-Weather (SWPC Kp index), NOTAMs, and Airspace restrictions.
Calculates cascading impacts and generates AI-assisted operational explanations.
"""

import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from db.models import Flight, TrajectoryPoint, Hazard, RiskAssessment
from module_1_trajectory.trajectory_service import calculate_distance_km

def evaluate_flight_risk(flight_id: str, db: Session) -> Dict[str, Any]:
    """
    Evaluates 4D trajectory points of a flight against all active hazards in the airspace.
    Calculates individual risk components, cascading multipliers, and overall risk score (0-100).
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise ValueError(f"Flight '{flight_id}' not found.")

    hazards = db.query(Hazard).filter(Hazard.is_active == True).all()
    waypoints = sorted(flight.waypoints, key=lambda w: w.sequence)

    weather_score = 0.0
    space_weather_score = 0.0
    notam_score = 0.0
    conflict_score = 0.0
    contributing_hazards = []
    cascading_factors = []

    # Iterate over waypoints to find proximity to hazards
    for wp in waypoints:
        wp_hazard_total = 0.0

        for h in hazards:
            dist_km = calculate_distance_km(wp.latitude, wp.longitude, h.center_latitude, h.center_longitude)

            # Check if within hazard impact radius
            if dist_km <= h.radius_km:
                # Vertical altitude overlap check
                alt_ft = wp.altitude_ft
                alt_overlap = (h.min_altitude_ft <= alt_ft <= h.max_altitude_ft)

                # Severity weighting
                sev_weight = {"LOW": 15.0, "MEDIUM": 35.0, "HIGH": 65.0, "SEVERE": 90.0}.get(h.severity, 40.0)
                # Proximity decay: higher impact closer to center
                proximity_factor = max(0.2, (1.0 - (dist_km / max(h.radius_km, 1.0))))
                leg_impact = sev_weight * proximity_factor

                if h.hazard_type == "WEATHER":
                    if alt_overlap:
                        weather_score = max(weather_score, leg_impact)
                        wp.weather_hazard = f"{h.title} (dist {int(dist_km)}km)"
                        wp.is_hotspot = True
                        if h.id not in contributing_hazards:
                            contributing_hazards.append(h.id)
                            cascading_factors.append(f"Weather hazard '{h.title}' active within {int(dist_km)}km of waypoint {wp.waypoint_name}.")

                elif h.hazard_type == "SPACE_WEATHER":
                    space_weather_score = max(space_weather_score, leg_impact * 0.8)
                    kp = (h.raw_payload or {}).get("kp_index", 5.0)
                    wp.space_weather_kp = kp
                    if h.id not in contributing_hazards:
                        contributing_hazards.append(h.id)
                        cascading_factors.append(f"Geomagnetic storm (Kp={kp}) affects avionics and HF coms at cruising altitude.")

                elif h.hazard_type == "NOTAM":
                    notam_score = max(notam_score, leg_impact * 0.75)
                    wp.notam_conflict = f"{h.title[:30]}..."
                    if h.id not in contributing_hazards:
                        contributing_hazards.append(h.id)
                        cascading_factors.append(f"Active NOTAM notice '{h.title}' affects sector operations.")

                elif h.hazard_type == "AIRSPACE_CONFLICT":
                    conflict_score = max(conflict_score, leg_impact)
                    if h.id not in contributing_hazards:
                        contributing_hazards.append(h.id)
                        cascading_factors.append(f"Restricted airspace conflict '{h.title}' intersects corridor.")

                wp_hazard_total = max(wp_hazard_total, leg_impact)

        wp.hazard_score = round(wp_hazard_total, 1)

    # Cascading compound calculation:
    # If multiple severe hazards coincide, synergy increases operational risk
    base_score = (
        (weather_score * 0.40) +
        (space_weather_score * 0.20) +
        (notam_score * 0.20) +
        (conflict_score * 0.20)
    )

    synergy_multiplier = 1.0
    if weather_score > 60 and space_weather_score > 40:
        synergy_multiplier += 0.15
        cascading_factors.append("Compound Hazard: Severe turbulence combined with degraded HF radio communications degrades safe avoidance margins.")
    if weather_score > 60 and notam_score > 40:
        synergy_multiplier += 0.12
        cascading_factors.append("Compound Hazard: Diversion weather along en-route track coincides with destination runway unserviceability.")

    overall_risk = min(100.0, round(base_score * synergy_multiplier, 1))

    # Risk Band
    if overall_risk >= 65.0:
        risk_band = "CRITICAL"
        action = "Immediate multi-route recovery diversion required."
        flight.status = "Needs Recovery"
    elif overall_risk >= 35.0:
        risk_band = "ELEVATED"
        action = "Monitor sector evolution; evaluate alternative routing options."
        if flight.status != "Needs Recovery":
            flight.status = "Active"
    else:
        risk_band = "LOW"
        action = "Proceed on standard flight plan."
        if flight.status != "Needs Recovery":
            flight.status = "Active"

    flight.overall_risk_score = overall_risk
    flight.overall_risk_band = risk_band

    # Generate AI-assisted explanatory rationale
    ai_narrative = (
        f"4D Trajectory Multi-Hazard Assessment for flight {flight.call_sign} ({flight.origin} → {flight.destination}): "
        f"Assessed overall risk is {overall_risk}/100 ({risk_band}). "
        f"Primary contributing components include Weather ({round(weather_score, 1)}), "
        f"Space Weather ({round(space_weather_score, 1)}), NOTAMs ({round(notam_score, 1)}), "
        f"and Airspace Restrictions ({round(conflict_score, 1)}). "
    )
    if cascading_factors:
        ai_narrative += f"Operational impact analysis indicates: {' '.join(cascading_factors[:3])} "
    ai_narrative += f"Recommendation: {action}"

    # Update or create RiskAssessment record
    assessment_id = f"RISK-{flight.id}-{int(flight.overall_risk_score)}"
    assessment = db.query(RiskAssessment).filter(RiskAssessment.flight_id == flight.id).order_by(RiskAssessment.evaluated_at.desc()).first()
    if not assessment:
        assessment = RiskAssessment(
            id=assessment_id,
            flight_id=flight.id,
            risk_score=overall_risk,
            risk_band=risk_band,
            weather_score=round(weather_score, 1),
            space_weather_score=round(space_weather_score, 1),
            notam_score=round(notam_score, 1),
            conflict_score=round(conflict_score, 1),
            cascading_factors=cascading_factors,
            ai_explanation=ai_narrative,
            contributing_hazards=contributing_hazards,
            recommended_action=action,
        )
        db.add(assessment)
    else:
        assessment.risk_score = overall_risk
        assessment.risk_band = risk_band
        assessment.weather_score = round(weather_score, 1)
        assessment.space_weather_score = round(space_weather_score, 1)
        assessment.notam_score = round(notam_score, 1)
        assessment.conflict_score = round(conflict_score, 1)
        assessment.cascading_factors = cascading_factors
        assessment.ai_explanation = ai_narrative
        assessment.contributing_hazards = contributing_hazards
        assessment.recommended_action = action

    db.commit()

    return {
        "status": "success",
        "flight_id": flight.id,
        "overall_risk_score": overall_risk,
        "overall_risk_band": risk_band,
        "scores": {
            "weather": round(weather_score, 1),
            "space_weather": round(space_weather_score, 1),
            "notam": round(notam_score, 1),
            "conflict": round(conflict_score, 1),
        },
        "cascading_factors": cascading_factors,
        "ai_explanation": ai_narrative,
        "recommended_action": action,
        "contributing_hazard_count": len(contributing_hazards),
    }
