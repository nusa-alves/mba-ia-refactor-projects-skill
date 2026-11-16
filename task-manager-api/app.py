import datetime
import logging
from flask import Flask
from flask_cors import CORS
from config.settings import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp

def create_app(config_object=Settings):
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app, origins=app.config["CORS_ORIGINS"])
    db.init_app(app)
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()
    return app

app = create_app()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=app.config["DEBUG"], host=app.config["HOST"], port=app.config["PORT"])
