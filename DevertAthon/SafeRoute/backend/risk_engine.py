from math import hypot


# Vijayawada demonstration route, shared by the live location ingestion path.
EXPECTED_ROUTE = [
    (16.5014, 80.6467), (16.5034, 80.6463), (16.5057, 80.6469),
    (16.5086, 80.6443), (16.5117, 80.6384), (16.5146, 80.6320),
    (16.5168, 80.6250), (16.5186, 80.6190), (16.5201, 80.6148),
]
DESTINATION = EXPECTED_ROUTE[-1]


def _distance(first, second):
    return hypot(first[0] - second[0], first[1] - second[1])


def evaluate_risk(locations, high_risk):
    """Evaluate persisted GPS samples. This is also used by demo samples."""
    latest = locations[-1]
    point = (latest["latitude"], latest["longitude"])
    signals = ["Journey appears normal."]
    score = 15

    if min(_distance(point, route_point) for route_point in EXPECTED_ROUTE) > 0.002:
        score = max(score, 45)
        signals.append("Route deviation detected.")

    if len(locations) > 1:
        previous = locations[-2]
        previous_point = (previous["latitude"], previous["longitude"])
        elapsed_seconds = (latest["recorded_at"] - previous["recorded_at"]).total_seconds()
        if _distance(point, previous_point) < 0.00015 and elapsed_seconds >= 180:
            score = max(score, 70)
            signals.append("Unexpected prolonged stop detected.")
        if _distance(point, DESTINATION) > _distance(previous_point, DESTINATION) + 0.001:
            score = max(score, 90)
            signals.append("Wrong-direction movement detected.")

    return score, signals, score >= high_risk
