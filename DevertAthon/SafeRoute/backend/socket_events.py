def broadcast_ride_update(socketio, payload):
    socketio.emit("location_update", {
        "ride_id": payload["ride_id"],
        "location": payload["current_location"],
        "actual_route": payload["actual_route"],
        "timestamp": payload["timestamp"],
    })
    socketio.emit("risk_update", {
        "ride_id": payload["ride_id"],
        "risk_score": payload["risk_score"],
        "risk_level": payload["risk_level"],
        "signals": [signal["signal"] for signal in payload["signals"]],
        "status": payload["status"],
        "high_risk_threshold": payload["high_risk_threshold"],
    })


def broadcast_checkin_requested(socketio, payload):
    socketio.emit("check_in_requested", payload)


def broadcast_safety_alert(socketio, payload):
    socketio.emit("safety_alert", payload)
