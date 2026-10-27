"""
SQLAlchemy Models for SkyRisk Auditor.
Defines schemas for 4D Trajectories, Multi-Hazards, Recovery Routes, OFPs, Audits, and Users (RBAC).
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, Text, JSON, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from db.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "skyrisk_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="flight_dispatcher")  # flight_dispatcher, safety_analyst, security_auditor, met_analyst
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    dispatcher_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    last_login = Column(DateTime(timezone=True), nullable=True)

class Flight(Base):
    __tablename__ = "skyrisk_flights"

    id = Column(String(50), primary_key=True)  # e.g., PK-781, HIST-2026-001
    call_sign = Column(String(20), nullable=False, index=True)
    aircraft_type = Column(String(50), nullable=False, default="A320-200")
    origin = Column(String(10), nullable=False)  # ICAO, e.g. OPKC
    origin_name = Column(String(100), nullable=True)
    destination = Column(String(10), nullable=False)  # ICAO, e.g. OPLA
    destination_name = Column(String(100), nullable=True)
    alternate_airport = Column(String(10), nullable=True, default="OPIS")
    cruise_altitude_ft = Column(Integer, nullable=False, default=36000)
    cruise_speed_kts = Column(Integer, nullable=False, default=450)
    planned_departure_utc = Column(DateTime(timezone=True), default=utc_now)
    estimated_arrival_utc = Column(DateTime(timezone=True), nullable=True)
    route_string = Column(Text, nullable=True)
    status = Column(String(30), default="Planned")  # Planned, Active, Needs Recovery, Cleared, Diverted
    phase = Column(String(30), default="Pre-flight")  # Pre-flight, Climb, En-route, Descent
    overall_risk_score = Column(Float, default=0.0)
    overall_risk_band = Column(String(20), default="LOW")  # LOW, ELEVATED, CRITICAL
    monitoring_active = Column(Boolean, default=True)
    active_recovery_id = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    waypoints = relationship("TrajectoryPoint", back_populates="flight", cascade="all, delete-orphan", order_by="TrajectoryPoint.sequence")
    recovery_plans = relationship("RecoveryPlan", back_populates="flight", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="flight", cascade="all, delete-orphan")

class TrajectoryPoint(Base):
    __tablename__ = "skyrisk_trajectory_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(String(50), ForeignKey("skyrisk_flights.id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    waypoint_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_ft = Column(Integer, nullable=False)
    time_offset_min = Column(Integer, nullable=False, default=0)
    heading_deg = Column(Float, default=0.0)
    speed_kts = Column(Float, default=450.0)
    is_hotspot = Column(Boolean, default=False)
    hazard_score = Column(Float, default=0.0)
    weather_hazard = Column(String(100), nullable=True)
    space_weather_kp = Column(Float, default=0.0)
    notam_conflict = Column(String(100), nullable=True)

    flight = relationship("Flight", back_populates="waypoints")

class Hazard(Base):
    __tablename__ = "skyrisk_hazards"

    id = Column(String(50), primary_key=True)  # HAZ-WX-01, HAZ-SW-01, NOTAM-OPLA-01
    hazard_type = Column(String(30), nullable=False)  # WEATHER, SPACE_WEATHER, NOTAM, AIRSPACE_CONFLICT
    title = Column(String(150), nullable=False)
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, SEVERE
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_km = Column(Float, default=50.0)
    min_altitude_ft = Column(Integer, default=0)
    max_altitude_ft = Column(Integer, default=60000)
    effective_start = Column(DateTime(timezone=True), default=utc_now)
    effective_end = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=False)
    raw_payload = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

class RiskAssessment(Base):
    __tablename__ = "skyrisk_assessments"

    id = Column(String(50), primary_key=True)
    flight_id = Column(String(50), ForeignKey("skyrisk_flights.id"), nullable=False, index=True)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_band = Column(String(20), nullable=False)  # LOW, ELEVATED, CRITICAL
    weather_score = Column(Float, default=0.0)
    space_weather_score = Column(Float, default=0.0)
    notam_score = Column(Float, default=0.0)
    conflict_score = Column(Float, default=0.0)
    cascading_factors = Column(JSON, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    contributing_hazards = Column(JSON, nullable=True)
    recommended_action = Column(String(100), nullable=True)

    flight = relationship("Flight", back_populates="risk_assessments")

class RecoveryPlan(Base):
    __tablename__ = "skyrisk_recovery_plans"

    id = Column(String(50), primary_key=True)  # REC-PK781-A
    flight_id = Column(String(50), ForeignKey("skyrisk_flights.id"), nullable=False, index=True)
    candidate_code = Column(String(10), nullable=False)  # ROUTE_A, ROUTE_B, ROUTE_C, ROUTE_D
    strategy_name = Column(String(100), nullable=False)  # e.g. "Minimum Delay (Shortest Route)"
    route_description = Column(Text, nullable=False)
    waypoints_json = Column(JSON, nullable=False)
    distance_change_km = Column(Float, default=0.0)
    delay_minutes = Column(Float, default=0.0)
    fuel_delta_kg = Column(Float, default=0.0)
    fuel_delta_percent = Column(Float, default=0.0)
    original_risk_score = Column(Float, default=0.0)
    residual_risk_score = Column(Float, default=0.0)
    risk_reduction_percent = Column(Float, default=0.0)
    status = Column(String(30), default="PENDING_APPROVAL")  # PENDING_APPROVAL, APPROVED, REJECTED
    approved_by = Column(String(100), nullable=True)
    approved_role = Column(String(50), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utc_now)

    flight = relationship("Flight", back_populates="recovery_plans")

class OperationalFlightPlan(Base):
    __tablename__ = "skyrisk_ofps"

    id = Column(String(50), primary_key=True)  # OFP-PK781-UPDATED-V2
    flight_id = Column(String(50), nullable=False, index=True)
    recovery_plan_id = Column(String(50), nullable=True)
    version = Column(Integer, default=1)
    status = Column(String(30), default="APPROVED_RELEASE")  # DRAFT, APPROVED_RELEASE, SUPERSEDED
    dispatch_notes = Column(Text, nullable=True)
    route_text = Column(Text, nullable=False)
    cruise_fl = Column(String(10), default="FL360")
    block_fuel_kg = Column(Float, default=9500.0)
    trip_fuel_kg = Column(Float, default=6800.0)
    contingency_fuel_kg = Column(Float, default=500.0)
    alternate_fuel_kg = Column(Float, default=1200.0)
    reserve_fuel_kg = Column(Float, default=1000.0)
    estimated_time_enroute_min = Column(Integer, default=110)
    dispatcher_signature = Column(String(100), nullable=True)
    signed_at = Column(DateTime(timezone=True), default=utc_now)
    navlog_data = Column(JSON, nullable=True)

class AuditEvent(Base):
    __tablename__ = "skyrisk_audit_trail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)
    actor_name = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)  # ROUTE_APPROVED, ROUTE_REJECTED, FLIGHT_CREATED, HAZARD_FLAGGED, OFP_GENERATED
    entity_type = Column(String(50), nullable=False)  # FLIGHT, RECOVERY, OFP, HAZARD, SYSTEM
    entity_id = Column(String(50), nullable=False)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    details = Column(Text, nullable=False)
    ip_address = Column(String(50), default="127.0.0.1")
    payload_hash = Column(String(64), nullable=False)  # SHA-256 tamper-evident digest
