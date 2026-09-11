from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from config import Config
from database import close_db, init_db
from routes import api


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=list(app.config["CORS_ORIGINS"]))
    app.teardown_appcontext(close_db)
    app.register_blueprint(api)
    with app.app_context():
        init_db()
    return app


app = create_app()
socketio = SocketIO(app, cors_allowed_origins=list(app.config["CORS_ORIGINS"]), async_mode="threading")
app.extensions["socketio"] = socketio


if __name__ == "__main__":
    # Background demo tasks must survive while the development server is running.
    socketio.run(app, host="127.0.0.1", port=5000, debug=app.config["DEBUG"], use_reloader=False)
