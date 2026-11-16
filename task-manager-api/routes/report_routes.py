from flask import Blueprint
from controllers import report_controller as controller
from middlewares.auth import require_admin

report_bp = Blueprint("reports", __name__)

report_bp.add_url_rule('/reports/summary', endpoint='summary_report', view_func=require_admin(controller.summary_report), methods=['GET'])
report_bp.add_url_rule('/reports/user/<int:user_id>', endpoint='user_report', view_func=require_admin(controller.user_report), methods=['GET'])
report_bp.add_url_rule('/categories', endpoint='get_categories', view_func=controller.get_categories, methods=['GET'])
report_bp.add_url_rule('/categories', endpoint='create_category', view_func=controller.create_category, methods=['POST'])
report_bp.add_url_rule('/categories/<int:cat_id>', endpoint='update_category', view_func=controller.update_category, methods=['PUT'])
report_bp.add_url_rule('/categories/<int:cat_id>', endpoint='delete_category', view_func=require_admin(controller.delete_category), methods=['DELETE'])
