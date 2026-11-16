import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from database import db
from middlewares.errors import ApiError

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        db.session.rollback()
        logger.exception('Database operation failed')
        return jsonify({'error': 'Erro interno'}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        logger.exception('Unhandled application error')
        return jsonify({'error': 'Erro interno'}), 500
