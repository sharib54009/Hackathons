from datetime import datetime, timedelta, timezone
import json
from urllib.request import Request, urlopen

def run_safety_incident_simulation(ride_id, socketio, api_base_url, step_seconds):
    """Post each demo stage as GPS would, allowing the UI to show progression."""
    start = datetime.now(timezone.utc)
    samples = [
        # Stage 1: normal journey remains SAFE.
        (16.5057, 80.6469, start),
        # Stage 2: move off the planned route, producing ELEVATED risk.
        (16.5080, 80.6400, start + timedelta(seconds=30)),
        # Stage 3: remain stationary for four simulated minutes.
        (16.5080, 80.6400, start + timedelta(minutes=4)),
        # Stage 4: move away from the destination, producing HIGH risk.
        (16.4950, 80.6850, start + timedelta(minutes=5)),
    ]
    for latitude, longitude, recorded_at in samples:
        body = json.dumps({"latitude": latitude, "longitude": longitude, "recorded_at": recorded_at.isoformat()}).encode()
        request = Request(
            f"{api_base_url}/api/rides/{ride_id}/locations",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10):
            pass
        socketio.sleep(step_seconds)
