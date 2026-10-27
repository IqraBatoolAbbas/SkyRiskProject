"""
Continuous 4D Airspace Risk & Conflict Monitoring Service.
Monitors all airborne and planned flights continuously over time.
Detects:
1. Emerging multi-hazards along updated flight trajectories.
2. 4D Flight-to-Flight separation conflicts (loss of separation alert).
3. Dynamic hazard intrusions (convective cell growth, new NOTAM restrictions).
"""

from datetime import datetime, timezone
import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from db.models import Flight, TrajectoryPoint, Hazard, AuditEvent
from module_1_trajectory.trajectory_service import calculate_distance_km
from module_2_risk_hazards.risk_service import evaluate_flight_risk

def run_airspace_monitoring_scan(db: Session) -> Dict[str, Any]:
    """
    Scans all active monitored flights in the airspace.
    Checks multi-hazard exposure and detects pairwise flight separation conflicts.
    """
    flights = db.query(Flight).filter(Flight.monitoring_active == True).all()
    hazards = db.query(Hazard).filter(Hazard.is_active == True).all()

    now = datetime.now(timezone.utc)
    scanned_flights = []
    conflict_alerts = []
    high_risk_flights = []

    # 1. Multi-hazard risk re-evaluation for each flight
    for f in flights:
        eval_res = evaluate_flight_risk(f.id, db)
        scanned_flights.append({
            "flight_id": f.id,
            "call_sign": f.call_sign,
            "origin": f.origin,
            "destination": f.destination,
            "status": f.status,
            "risk_score": eval_res["overall_risk_score"],
            "risk_band": eval_res["overall_risk_band"],
            "cascading_factors": eval_res["cascading_factors"][:2],
        })
        if eval_res["overall_risk_score"] >= 65.0:
            high_risk_flights.append({
                "flight_id": f.id,
                "call_sign": f.call_sign,
                "risk_score": eval_res["overall_risk_score"],
                "reason": eval_res["recommended_action"],
            })

    # 2. Pairwise 4D Flight-to-Flight Separation Conflict Detection
    # Standard en-route radar separation minimum: 10 NM (~18.5 km) and 1000 ft vertical
    for i in range(len(flights)):
        for j in range(i + 1, len(flights)):
            f1 = flights[i]
            f2 = flights[j]

            # Get latest or representative active waypoints
            wps1 = sorted(f1.waypoints, key=lambda w: w.sequence)
            wps2 = sorted(f2.waypoints, key=lambda w: w.sequence)

            for p1 in wps1:
                for p2 in wps2:
                    # Check temporal time window overlap (+/- 15 minutes)
                    if abs(p1.time_offset_min - p2.time_offset_min) <= 15:
                        dist_km = calculate_distance_km(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
                        alt_diff = abs(p1.altitude_ft - p2.altitude_ft)

                        if dist_km < 35.0 and alt_diff < 1500 and p1.altitude_ft > 5000:
                            conflict_alert = {
                                "id": f"CONF-{f1.call_sign}-{f2.call_sign}",
                                "flight_a": f1.call_sign,
                                "flight_b": f2.call_sign,
                                "lateral_dist_km": round(dist_km, 1),
                                "vertical_diff_ft": alt_diff,
                                "waypoint_sector": f"{p1.waypoint_name} / {p2.waypoint_name}",
                                "severity": "CRITICAL" if dist_km < 18.5 else "WARNING",
                                "message": f"Loss of separation advisory: {f1.call_sign} and {f2.call_sign} converge within {round(dist_km, 1)}km at FL{p1.altitude_ft//100}.",
                            }
                            conflict_alerts.append(conflict_alert)
                            break

    return {
        "status": "success",
        "timestamp_utc": now.isoformat(),
        "total_monitored_flights": len(flights),
        "high_risk_flight_count": len(high_risk_flights),
        "separation_conflicts_count": len(conflict_alerts),
        "scanned_flights": scanned_flights,
        "conflict_alerts": conflict_alerts,
        "high_risk_flights": high_risk_flights,
        "monitoring_frequency": "Continuous 4D scan active",
    }
