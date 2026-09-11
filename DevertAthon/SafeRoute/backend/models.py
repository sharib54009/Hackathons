from dataclasses import dataclass


@dataclass(frozen=True)
class Ride:
    id: str
    rider_name: str
    origin: str
    destination: str
    trusted_contact: str
    status: str
    risk_score: int
    risk_level: str
    created_at: str | None = None
