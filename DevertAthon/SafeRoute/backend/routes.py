from uuid import uuid4

import json
from datetime import datetime
from threading import Thread

from flask import Blueprint, current_app, jsonify, request

from database import get_db
from models import Ride
from risk_engine import EXPECTED_ROUTE, evaluate_risk
from socket_events import broadcast_checkin_requested, broadcast_ride_update, broadcast_safety_alert

api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@api.post("/rides")
def create_ride():
    payload = request.get_json(silent=True) or {}
    fields = ("rider_name", "origin", "destination", "trusted_contact")
    missing = [field for field in fields if not isinstance(payload.get(field), str) or not payload[field].strip()]
    if missing:
        return jsonify({"error": "Please provide rider name, origin, destination, and trusted contact."}), 400

    ride = Ride(
        id=str(uuid4()),
        rider_name=payload["rider_name"].strip(),
        origin=payload["origin"].strip(),
        destination=payload["destination"].strip(),
        trusted_contact=payload["trusted_contact"].strip(),
        status="active",
        risk_score=0,
        risk_level="SAFE",
    )
    get_db().execute(
        """INSERT INTO rides (id, rider_name, origin, destination, trusted_contact, status, risk_score, risk_level)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (ride.id, ride.rider_name, ride.origin, ride.destination, ride.trusted_contact, ride.status, ride.risk_score, ride.risk_level),
    )
    get_db().commit()
    return jsonify({"ride_id": ride.id, "status": ride.status, "risk_score": ride.risk_score, "risk_level": ride.risk_level}), 201


def _parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _ride_update(ride_id):
    db = get_db()
    ride = db.execute("SELECT * FROM rides WHERE id = ?", (ride_id,)).fetchone()
    locations = db.execute(
        "SELECT latitude, longitude, recorded_at FROM ride_locations WHERE ride_id = ? ORDER BY id", (ride_id,)
    ).fetchall()
    signals = db.execute(
        "SELECT signal, detected_at FROM ride_signals WHERE ride_id = ? ORDER BY id", (ride_id,)
    ).fetchall()
    return {
        "ride_id": ride["id"], "rider_name": ride["rider_name"], "status": ride["status"],
        "risk_score": ride["risk_score"], "risk_level": ride["risk_level"],
        "current_location": dict(locations[-1]) if locations else None,
        "expected_route": [{"latitude": lat, "longitude": lng} for lat, lng in EXPECTED_ROUTE],
        "actual_route": [dict(point) for point in locations],
        "signals": [dict(signal) for signal in signals],
        "timestamp": locations[-1]["recorded_at"] if locations else ride["created_at"],
        "high_risk_threshold": current_app.config["HIGH_RISK"],
    }


def _alert_payload(update, alert_type, message):
    location = update["current_location"] or {}
    return {
        "ride_id": update["ride_id"],
        "rider_name": update["rider_name"],
        "risk_score": update["risk_score"],
        "risk_level": update["risk_level"],
        "current_location": location,
        "signals": [signal["signal"] for signal in update["signals"]],
        "timestamp": update["timestamp"],
        "message": message,
        "alert_type": alert_type,
    }


def _create_safety_alert(update, alert_type, message):
    payload = _alert_payload(update, alert_type, message)
    location = payload["current_location"]
    get_db().execute(
        """INSERT INTO safety_alerts
           (id, ride_id, alert_type, rider_name, risk_score, risk_level, latitude, longitude, signals, occurred_at, message)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(uuid4()), payload["ride_id"], alert_type, payload["rider_name"], payload["risk_score"],
            payload["risk_level"], location.get("latitude"), location.get("longitude"),
            json.dumps(payload["signals"]), payload["timestamp"], message,
        ),
    )
    get_db().commit()
    broadcast_safety_alert(current_app.extensions["socketio"], payload)
    return payload


@api.post("/rides/<ride_id>/locations")
def ingest_location(ride_id):
    payload = request.get_json(silent=True) or {}
    try:
        latitude = float(payload["latitude"])
        longitude = float(payload["longitude"])
        recorded_at = _parse_timestamp(payload["recorded_at"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "latitude, longitude, and an ISO timestamp are required."}), 400

    db = get_db()
    ride = db.execute("SELECT * FROM rides WHERE id = ?", (ride_id,)).fetchone()
    if not ride:
        return jsonify({"error": "Ride not found."}), 404
    previous_level = ride["risk_level"]
    db.execute(
        "INSERT INTO ride_locations (ride_id, latitude, longitude, recorded_at) VALUES (?, ?, ?, ?)",
        (ride_id, latitude, longitude, recorded_at.isoformat()),
    )
    rows = db.execute(
        "SELECT latitude, longitude, recorded_at FROM ride_locations WHERE ride_id = ? ORDER BY id", (ride_id,)
    ).fetchall()
    locations = [{**dict(row), "recorded_at": _parse_timestamp(row["recorded_at"])} for row in rows]
    score, new_signals, is_high_risk = evaluate_risk(locations, current_app.config["HIGH_RISK"])
    level = "HIGH" if is_high_risk else "ELEVATED" if score >= 40 else "SAFE"
    status = "high-risk" if is_high_risk else "active"
    db.execute("UPDATE rides SET status = ?, risk_score = ?, risk_level = ? WHERE id = ?", (status, score, level, ride_id))
    for signal in new_signals:
        db.execute(
            "INSERT OR IGNORE INTO ride_signals (ride_id, signal, detected_at) VALUES (?, ?, ?)",
            (ride_id, signal, recorded_at.isoformat()),
        )
    db.commit()
    update = _ride_update(ride_id)
    broadcast_ride_update(current_app.extensions["socketio"], update)
    if level == "ELEVATED" and previous_level != "ELEVATED":
        checkin = {
            "ride_id": ride_id,
            "message": "Are you safe?",
            "requested_at": update["timestamp"],
        }
        db.execute(
            "INSERT OR REPLACE INTO ride_checkins (ride_id, status, response, requested_at, resolved_at) VALUES (?, ?, ?, ?, ?)",
            (ride_id, "active", None, update["timestamp"], None),
        )
        db.commit()
        broadcast_checkin_requested(current_app.extensions["socketio"], checkin)
    high_alert_exists = db.execute(
        "SELECT 1 FROM safety_alerts WHERE ride_id = ? AND alert_type = 'high_risk' LIMIT 1", (ride_id,)
    ).fetchone()
    if is_high_risk and not high_alert_exists:
        _create_safety_alert(update, "high_risk", "High-risk journey detected. Please check on the rider.")
    return jsonify(update)


@api.post("/rides/<ride_id>/check-ins/respond")
def respond_to_checkin(ride_id):
    payload = request.get_json(silent=True) or {}
    response = payload.get("response")
    if response not in {"safe", "help", "cannot_respond"}:
        return jsonify({"error": "A valid check-in response is required."}), 400
    db = get_db()
    ride = db.execute("SELECT id FROM rides WHERE id = ?", (ride_id,)).fetchone()
    checkin = db.execute("SELECT * FROM ride_checkins WHERE ride_id = ? AND status = 'active'", (ride_id,)).fetchone()
    if not ride or not checkin:
        return jsonify({"error": "No active safety check-in found."}), 404
    now = datetime.utcnow().isoformat() + "Z"
    db.execute("UPDATE ride_checkins SET status = 'resolved', response = ?, resolved_at = ? WHERE ride_id = ?", (response, now, ride_id))
    db.commit()
    update = _ride_update(ride_id)
    if response == "help":
        _create_safety_alert(update, "rider_help", "The rider requested immediate help.")
    elif response == "cannot_respond" and update["risk_level"] in {"ELEVATED", "HIGH"}:
        _create_safety_alert(update, "rider_unresponsive", "The rider could not respond to a safety check-in.")
    return jsonify({"status": "resolved", "response": response})


@api.post("/rides/<ride_id>/sos")
def manual_sos(ride_id):
    if not get_db().execute("SELECT id FROM rides WHERE id = ?", (ride_id,)).fetchone():
        return jsonify({"error": "Ride not found."}), 404
    update = _ride_update(ride_id)
    alert = _create_safety_alert(update, "manual_sos", "The rider manually requested emergency help.")
    return jsonify(alert), 201


@api.post("/rides/<ride_id>/simulate-safety-incident")
def simulate_safety_incident(ride_id):
    if not get_db().execute("SELECT id FROM rides WHERE id = ?", (ride_id,)).fetchone():
        return jsonify({"error": "Ride not found."}), 404
    socketio = current_app.extensions["socketio"]
    from simulator import run_safety_incident_simulation
    Thread(
        target=run_safety_incident_simulation,
        args=(ride_id, socketio, current_app.config["LOCAL_API_BASE_URL"], current_app.config["SIMULATION_STEP_SECONDS"]),
        daemon=True,
    ).start()
    return jsonify({"status": "simulation_started", "ride_id": ride_id}), 202
