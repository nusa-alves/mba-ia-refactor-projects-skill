import logging

from flask import jsonify

from controllers.errors import ApiError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({"erro": error.message}), error.status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Erro não tratado", exc_info=error)
        return jsonify({"erro": "Erro interno do servidor"}), 500

