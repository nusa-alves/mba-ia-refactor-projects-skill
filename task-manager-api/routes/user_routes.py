from flask import Blueprint
from controllers import user_controller as controller
from middlewares.auth import require_admin

user_bp = Blueprint("users", __name__)

user_bp.add_url_rule('/users', endpoint='get_users', view_func=controller.get_users, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', endpoint='get_user', view_func=controller.get_user, methods=['GET'])
user_bp.add_url_rule('/users', endpoint='create_user', view_func=controller.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', endpoint='update_user', view_func=require_admin(controller.update_user), methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', endpoint='delete_user', view_func=require_admin(controller.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', endpoint='get_user_tasks', view_func=controller.get_user_tasks, methods=['GET'])
user_bp.add_url_rule('/login', endpoint='login', view_func=controller.login, methods=['POST'])
