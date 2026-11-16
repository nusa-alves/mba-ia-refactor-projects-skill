import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import close_db, init_db
from middlewares.error_handler import register_error_handlers
from routes.api_routes import api


def create_app(settings=Settings):
    application = Flask(__name__)
    application.config.from_object(settings)
    application.register_blueprint(api)
    application.teardown_appcontext(close_db)
    if application.config["CORS_ORIGINS"]:
        CORS(application, origins=application.config["CORS_ORIGINS"])
    register_error_handlers(application)
    logging.basicConfig(level=logging.INFO)
    with application.app_context():
        init_db()
    return application


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
        use_reloader=False,
    )

