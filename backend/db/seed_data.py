"""
Seed Data Generator for SkyRisk Auditor.
Initializes tables and populates realistic 4D trajectories, multi-hazards,
audit trails, and RBAC user accounts according to the Project Proposal.
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db.connection import Base, engine, SessionLocal
from db.models import (
    User, Flight, TrajectoryPoint, Hazard, RiskAssessment,
    RecoveryPlan, OperationalFlightPlan, AuditEvent
)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(f"skyrisk_salt_{pw}".encode()).hexdigest()

def compute_hash(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()

def seed_database():
    print("Initializing SkyRisk Auditor PostgreSQL tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        print("Seeding RBAC Users (Flight Dispatcher, Safety Analyst, Security Auditor, Met Analyst)...")

        users = [
            User(
                username="dispatcher_ayesha",
                full_name="Ayesha Rahman",
                email="ayesha.rahman@skyrisk.aero",
                role="flight_dispatcher",
                dispatcher_id="DISP-PK-891",
                password_hash=hash_pw("dispatch123"),
                is_active=True,
            ),
            User(
                username="safety_tariq",
                full_name="Tariq Mehmood",
                email="tariq.mehmood@skyrisk.aero",
                role="safety_analyst",
                dispatcher_id="SAFE-ANA-402",
                password_hash=hash_pw("safety123"),
                is_active=True,
            ),
            User(
                username="auditor_zainab",
                full_name="Zainab Fatima",
                email="zainab.fatima@skyrisk.aero",
                role="security_auditor",
                dispatcher_id="AUD-SEC-109",
                password_hash=hash_pw("audit123"),
                is_active=True,
            ),
            User(
                username="met_farhan",
                full_name="Farhan Ali",
                email="farhan.ali@skyrisk.aero",
                role="met_analyst",
                dispatcher_id="MET-OPS-773",
                password_hash=hash_pw("weather123"),
                is_active=True,
            ),
        ]
        session.add_all(users)

        print("Seeding Active Airspace Multi-Hazards...")
        hazards = [
            Hazard(
                id="HAZ-WX-MULTAN-01",
                hazard_type="WEATHER",
                title="Severe Convective Thunderstorm & Microburst (Multan Sector)",
                severity="SEVERE",
                center_latitude=30.19,
                center_longitude=71.43,
                radius_km=75.0,
                min_altitude_ft=18000,
                max_altitude_ft=43000,
                effective_start=now - timedelta(hours=2),
                effective_end=now + timedelta(hours=6),
                description="Intense CB cluster with heavy precipitation, severe icing between FL240-FL360, and strong convective downdrafts exceeding 45 knots.",
                raw_payload={"radar_dbz": 54, "turbulence_edr": 0.48, "icing_index": 0.85, "cloud_top_fl": 430},
            ),
            Hazard(
                id="HAZ-SWPC-KP7",
                hazard_type="SPACE_WEATHER",
                title="NOAA SWPC Strong Geomagnetic Storm (Kp=6.7, Class G3)",
                severity="HIGH",
                center_latitude=33.5,
                center_longitude=73.1,
                radius_km=450.0,
                min_altitude_ft=28000,
                max_altitude_ft=60000,
                effective_start=now - timedelta(hours=4),
                effective_end=now + timedelta(hours=12),
                description="Elevated solar energetic proton flux. HF radio degradation across Northern FIRs, GPS L1 positioning error margin widened by 18 meters.",
                raw_payload={"kp_index": 6.7, "solar_flux": 182, "hf_attenuation_db": 14.2, "alert_level": "WARNING"},
            ),
            Hazard(
                id="NOTAM-OPLA-RWY-02",
                hazard_type="NOTAM",
                title="NOTAM A0482/26: OPLA Primary Runway 36R Closed For Emergency Maintenance",
                severity="HIGH",
                center_latitude=31.52,
                center_longitude=74.40,
                radius_km=25.0,
                min_altitude_ft=0,
                max_altitude_ft=5000,
                effective_start=now - timedelta(hours=1),
                effective_end=now + timedelta(hours=8),
                description="RWY 36R/18L U/S DUE TO SURFACE CRACK REPAIRS. ALL ARRIVALS DIVERT TO RWY 36L. EXPECT 20 MINUTE ATC FLOW HOLDING DELAYS.",
                raw_payload={"notam_number": "A0482/26", "location": "OPLA", "classification": "RUNWAY_CLOSURE", "confidence": 96.4},
            ),
            Hazard(
                id="HAZ-AIRSPACE-TFR-88",
                hazard_type="AIRSPACE_CONFLICT",
                title="Temporary Flight Restriction (TFR) Military Air Exercise Sector Delta",
                severity="SEVERE",
                center_latitude=28.75,
                center_longitude=70.10,
                radius_km=60.0,
                min_altitude_ft=0,
                max_altitude_ft=45000,
                effective_start=now - timedelta(hours=1),
                effective_end=now + timedelta(hours=5),
                description="Active military tactical airspace. Civilian crossing strictly prohibited without direct ATC tactical clearance.",
                raw_payload={"tfr_code": "TFR-PAK-MIL-D", "controlling_agency": "Lahore ACC"},
            ),
        ]
        session.add_all(hazards)

        print("Seeding Flights and 4D Trajectories...")

        # Flight 1: PK-781 (Karachi -> Lahore)
        f1 = Flight(
            id="PK-781",
            call_sign="PK-781",
            aircraft_type="A320-200 (AP-BLD)",
            origin="OPKC",
            origin_name="Jinnah Intl, Karachi",
            destination="OPLA",
            destination_name="Allama Iqbal Intl, Lahore",
            alternate_airport="OPIS",
            cruise_altitude_ft=36000,
            cruise_speed_kts=460,
            planned_departure_utc=now - timedelta(minutes=40),
            estimated_arrival_utc=now + timedelta(minutes=70),
            route_string="OPKC DCT RK J121 SULOM J130 OPLA",
            status="Needs Recovery",
            phase="En-route",
            overall_risk_score=78.5,
            overall_risk_band="CRITICAL",
            monitoring_active=True,
        )
        session.add(f1)
        session.flush()

        # 4D Waypoints for PK-781
        pk781_points = [
            TrajectoryPoint(flight_id=f1.id, sequence=1, waypoint_name="OPKC", latitude=24.90, longitude=67.16, altitude_ft=0, time_offset_min=0, heading_deg=45.0, speed_kts=160, is_hotspot=False, hazard_score=5.0),
            TrajectoryPoint(flight_id=f1.id, sequence=2, waypoint_name="RK (Rahim Yar Khan)", latitude=28.42, longitude=70.30, altitude_ft=36000, time_offset_min=35, heading_deg=35.0, speed_kts=460, is_hotspot=False, hazard_score=18.0),
            TrajectoryPoint(flight_id=f1.id, sequence=3, waypoint_name="SULOM (Multan Sector)", latitude=30.15, longitude=71.45, altitude_ft=36000, time_offset_min=55, heading_deg=32.0, speed_kts=440, is_hotspot=True, hazard_score=88.5, weather_hazard="Severe CB & Microburst", space_weather_kp=5.2, notam_conflict="Nearby Sector Hold"),
            TrajectoryPoint(flight_id=f1.id, sequence=4, waypoint_name="TRK (Toba Tek Singh)", latitude=30.97, longitude=72.48, altitude_ft=28000, time_offset_min=75, heading_deg=38.0, speed_kts=420, is_hotspot=False, hazard_score=35.0),
            TrajectoryPoint(flight_id=f1.id, sequence=5, waypoint_name="OPLA", latitude=31.52, longitude=74.40, altitude_ft=0, time_offset_min=110, heading_deg=42.0, speed_kts=140, is_hotspot=False, hazard_score=24.0, notam_conflict="RWY 36R Closed"),
        ]
        session.add_all(pk781_points)

        # Risk Assessment for PK-781
        risk1 = RiskAssessment(
            id="RISK-PK781-001",
            flight_id=f1.id,
            evaluated_at=now,
            risk_score=78.5,
            risk_band="CRITICAL",
            weather_score=88.0,
            space_weather_score=54.0,
            notam_score=62.0,
            conflict_score=40.0,
            cascading_factors=[
                "Convective storm cell exactly intercepts airway J121 at waypoint SULOM.",
                "High severe turbulence (EDR 0.48) forces structural airframe speed reduction.",
                "Space weather Kp=6.7 reduces backup VHF/HF margin, preventing safe radar handoff blind spots.",
                "Destination OPLA Runway 36R closure imposes additional 20-min holding fuel exposure."
            ],
            ai_explanation="Flight PK-781 is currently projected to penetrate a severe convective cloud cluster (54 dBZ) with cloud tops reaching FL430 near Multan. Combined with elevated geomagnetic radiation and destination single-runway restrictions, continuation along original flight plan creates critical hazard risk (78.5/100). Immediate multi-route recovery diversion is recommended.",
            contributing_hazards=["HAZ-WX-MULTAN-01", "HAZ-SWPC-KP7", "NOTAM-OPLA-RWY-02"],
            recommended_action="Execute lateral recovery route diversion around SULOM waypoint.",
        )
        session.add(risk1)

        # Candidate Recovery Routes for PK-781 (The 4 algorithmic recovery routes)
        recovery_candidates = [
            RecoveryPlan(
                id="REC-PK781-ROUTEA",
                flight_id=f1.id,
                candidate_code="ROUTE_A",
                strategy_name="Minimum Delay (Shortest Tactical Detour)",
                route_description="Lateral detour 25 NM East of SULOM cell via waypoint BAHWL, returning to airway J130 at TRK.",
                waypoints_json=[
                    {"name": "OPKC", "lat": 24.90, "lon": 67.16, "alt": 36000, "time_min": 0},
                    {"name": "RK", "lat": 28.42, "lon": 70.30, "alt": 36000, "time_min": 35},
                    {"name": "BAHWL (Detour)", "lat": 29.39, "lon": 71.68, "alt": 36000, "time_min": 52},
                    {"name": "TRK", "lat": 30.97, "lon": 72.48, "alt": 28000, "time_min": 78},
                    {"name": "OPLA", "lat": 31.52, "lon": 74.40, "alt": 0, "time_min": 114},
                ],
                distance_change_km=32.4,
                delay_minutes=4.2,
                fuel_delta_kg=145.0,
                fuel_delta_percent=2.1,
                original_risk_score=78.5,
                residual_risk_score=24.2,
                risk_reduction_percent=69.2,
                status="PENDING_APPROVAL",
            ),
            RecoveryPlan(
                id="REC-PK781-ROUTEB",
                flight_id=f1.id,
                candidate_code="ROUTE_B",
                strategy_name="Minimum Fuel (Eco Step-Climb & Wind Assist)",
                route_description="Climb from FL360 to FL390 to overfly mid-level turbulence, banking west into favorable 45kt tailwind jet stream.",
                waypoints_json=[
                    {"name": "OPKC", "lat": 24.90, "lon": 67.16, "alt": 36000, "time_min": 0},
                    {"name": "RK", "lat": 28.42, "lon": 70.30, "alt": 39000, "time_min": 34},
                    {"name": "DGKHAN (High FL)", "lat": 30.05, "lon": 70.63, "alt": 39000, "time_min": 54},
                    {"name": "JHANG", "lat": 31.27, "lon": 72.33, "alt": 31000, "time_min": 76},
                    {"name": "OPLA", "lat": 31.52, "lon": 74.40, "alt": 0, "time_min": 112},
                ],
                distance_change_km=18.6,
                delay_minutes=2.1,
                fuel_delta_kg=-38.0,
                fuel_delta_percent=-0.5,
                original_risk_score=78.5,
                residual_risk_score=21.0,
                risk_reduction_percent=73.2,
                status="PENDING_APPROVAL",
            ),
            RecoveryPlan(
                id="REC-PK781-ROUTEC",
                flight_id=f1.id,
                candidate_code="ROUTE_C",
                strategy_name="Safest Route (Maximum Safety Buffer)",
                route_description="Wide 50 NM lateral bypass clearance keeping aircraft outside all precipitation radar returns and convective downdraft buffers.",
                waypoints_json=[
                    {"name": "OPKC", "lat": 24.90, "lon": 67.16, "alt": 36000, "time_min": 0},
                    {"name": "SUKKUR", "lat": 27.70, "lon": 68.85, "alt": 36000, "time_min": 28},
                    {"name": "SADIQ (Wide Buffer)", "lat": 28.25, "lon": 70.12, "alt": 36000, "time_min": 42},
                    {"name": "VEHARI (Safe)", "lat": 30.04, "lon": 72.35, "alt": 34000, "time_min": 68},
                    {"name": "OPLA", "lat": 31.52, "lon": 74.40, "alt": 0, "time_min": 124},
                ],
                distance_change_km=74.2,
                delay_minutes=14.0,
                fuel_delta_kg=380.0,
                fuel_delta_percent=5.6,
                original_risk_score=78.5,
                residual_risk_score=7.4,
                risk_reduction_percent=90.6,
                status="PENDING_APPROVAL",
            ),
            RecoveryPlan(
                id="REC-PK781-ROUTED",
                flight_id=f1.id,
                candidate_code="ROUTE_D",
                strategy_name="Balanced Operational Recovery (Recommended)",
                route_description="Pareto-optimal multi-objective trajectory balancing minor delay (+6m), acceptable fuel burn (+190kg), and safe risk reduction to 13.5.",
                waypoints_json=[
                    {"name": "OPKC", "lat": 24.90, "lon": 67.16, "alt": 36000, "time_min": 0},
                    {"name": "RK", "lat": 28.42, "lon": 70.30, "alt": 36000, "time_min": 35},
                    {"name": "KORAL (Offset 20NM)", "lat": 29.80, "lon": 71.90, "alt": 36000, "time_min": 56},
                    {"name": "OKARA", "lat": 30.80, "lon": 73.45, "alt": 26000, "time_min": 82},
                    {"name": "OPLA", "lat": 31.52, "lon": 74.40, "alt": 0, "time_min": 116},
                ],
                distance_change_km=42.0,
                delay_minutes=6.0,
                fuel_delta_kg=190.0,
                fuel_delta_percent=2.8,
                original_risk_score=78.5,
                residual_risk_score=13.5,
                risk_reduction_percent=82.8,
                status="PENDING_APPROVAL",
            ),
        ]
        session.add_all(recovery_candidates)

        # Flight 2: PK-302 (Karachi -> Islamabad)
        f2 = Flight(
            id="PK-302",
            call_sign="PK-302",
            aircraft_type="B777-200ER",
            origin="OPKC",
            origin_name="Jinnah Intl, Karachi",
            destination="OPIS",
            destination_name="Islamabad Intl, Islamabad",
            alternate_airport="OPLA",
            cruise_altitude_ft=38000,
            cruise_speed_kts=490,
            planned_departure_utc=now + timedelta(minutes=25),
            estimated_arrival_utc=now + timedelta(minutes=140),
            route_string="OPKC J121 NH J133 OPIS",
            status="Planned",
            phase="Pre-flight",
            overall_risk_score=42.0,
            overall_risk_band="ELEVATED",
            monitoring_active=True,
        )
        session.add(f2)

        # Flight 3: PK-211 (Peshawar -> Karachi)
        f3 = Flight(
            id="PK-211",
            call_sign="PK-211",
            aircraft_type="A320-200",
            origin="OPPS",
            origin_name="Bacha Khan Intl, Peshawar",
            destination="OPKC",
            destination_name="Jinnah Intl, Karachi",
            alternate_airport="OPNH",
            cruise_altitude_ft=34000,
            cruise_speed_kts=450,
            planned_departure_utc=now - timedelta(minutes=60),
            estimated_arrival_utc=now + timedelta(minutes=45),
            route_string="OPPS J133 RK J121 OPKC",
            status="Active",
            phase="En-route",
            overall_risk_score=18.4,
            overall_risk_band="LOW",
            monitoring_active=True,
        )
        session.add(f3)

        # Flight 4: EK-612 (Dubai -> Islamabad)
        f4 = Flight(
            id="EK-612",
            call_sign="EK-612",
            aircraft_type="B777-300ER",
            origin="OMDB",
            origin_name="Dubai Intl, UAE",
            destination="OPIS",
            destination_name="Islamabad Intl, Pakistan",
            alternate_airport="OPLA",
            cruise_altitude_ft=37000,
            cruise_speed_kts=485,
            planned_departure_utc=now - timedelta(minutes=90),
            estimated_arrival_utc=now + timedelta(minutes=50),
            route_string="OMDB PG OMAL PG G450 OPIS",
            status="Active",
            phase="En-route",
            overall_risk_score=36.0,
            overall_risk_band="ELEVATED",
            monitoring_active=True,
        )
        session.add(f4)

        # OFP Draft for PK-781
        ofp1 = OperationalFlightPlan(
            id="OFP-PK781-ORIGINAL",
            flight_id=f1.id,
            version=1,
            status="DRAFT",
            dispatch_notes="Initial scheduled flight release. Subject to re-clearance upon recovery route selection.",
            route_text="OPKC RK J121 SULOM J130 OPLA",
            cruise_fl="FL360",
            block_fuel_kg=9200.0,
            trip_fuel_kg=6800.0,
            contingency_fuel_kg=350.0,
            alternate_fuel_kg=1150.0,
            reserve_fuel_kg=900.0,
            estimated_time_enroute_min=110,
            dispatcher_signature="Ayesha Rahman (DISP-PK-891)",
            signed_at=now - timedelta(minutes=45),
        )
        session.add(ofp1)

        # Initial Audit Events
        audit_events = [
            AuditEvent(
                event_id="AUD-INIT-001",
                timestamp=now - timedelta(hours=1),
                actor_name="System Ingestion Engine",
                actor_role="system",
                action="HAZARD_INGESTION",
                entity_type="HAZARD",
                entity_id="HAZ-WX-MULTAN-01",
                details="Ingested Doppler weather radar convective cell data. Radar reflectivity peak 54 dBZ detected in Multan FIR corridor.",
                payload_hash=compute_hash({"hazard": "HAZ-WX-MULTAN-01", "dbz": 54}),
            ),
            AuditEvent(
                event_id="AUD-INIT-002",
                timestamp=now - timedelta(minutes=38),
                actor_name="Ayesha Rahman",
                actor_role="flight_dispatcher",
                action="TRAJECTORY_EVALUATION",
                entity_type="FLIGHT",
                entity_id="PK-781",
                details="Executed 4D Trajectory Multi-Hazard Risk Scan for PK-781. Overall risk score calculated at 78.5 (CRITICAL).",
                payload_hash=compute_hash({"flight": "PK-781", "score": 78.5}),
            ),
            AuditEvent(
                event_id="AUD-INIT-003",
                timestamp=now - timedelta(minutes=30),
                actor_name="SkyRisk Multi-Route Optimizer",
                actor_role="system",
                action="RECOVERY_CANDIDATES_GENERATED",
                entity_type="RECOVERY",
                entity_id="REC-PK781",
                details="Synthesized 4 candidate recovery options: Route A (Shortest), Route B (Eco/Min Fuel), Route C (Safest), Route D (Balanced). Awaiting Dispatcher Authorization.",
                payload_hash=compute_hash({"candidates": 4, "target": "PK-781"}),
            ),
        ]
        session.add_all(audit_events)

        session.commit()
        print("Database successfully seeded with realistic aviation data, RBAC users, and multi-hazards!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
