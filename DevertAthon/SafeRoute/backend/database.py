import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS rides (
            id TEXT PRIMARY KEY,
            rider_name TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            trusted_contact TEXT NOT NULL,
            status TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS ride_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (ride_id) REFERENCES rides(id)
        )
        """
    )
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS ride_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ride_id TEXT NOT NULL,
            signal TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            UNIQUE(ride_id, signal),
            FOREIGN KEY (ride_id) REFERENCES rides(id)
        )
        """
    )
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS safety_alerts (
            id TEXT PRIMARY KEY,
            ride_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            rider_name TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            signals TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ride_id) REFERENCES rides(id)
        )
        """
    )
    get_db().execute(
        """
        CREATE TABLE IF NOT EXISTS ride_checkins (
            ride_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            response TEXT,
            requested_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (ride_id) REFERENCES rides(id)
        )
        """
    )
    get_db().commit()
