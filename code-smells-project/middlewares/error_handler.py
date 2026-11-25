import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from controllers.errors import ApiError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({"erro": error.message}), error.status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return jsonify({"erro": error.name}), error.code
        logger.exception("Erro não tratado", exc_info=error)
        return jsonify({"erro": "Erro interno do servidor"}), 500

