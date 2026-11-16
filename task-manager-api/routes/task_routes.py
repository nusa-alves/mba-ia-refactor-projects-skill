from flask import Blueprint
from controllers import task_controller as controller
from middlewares.auth import require_admin

task_bp = Blueprint("tasks", __name__)

task_bp.add_url_rule('/tasks', endpoint='get_tasks', view_func=controller.get_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', endpoint='get_task', view_func=controller.get_task, methods=['GET'])
task_bp.add_url_rule('/tasks', endpoint='create_task', view_func=controller.create_task, methods=['POST'])
task_bp.add_url_rule('/tasks/<int:task_id>', endpoint='update_task', view_func=controller.update_task, methods=['PUT'])
task_bp.add_url_rule('/tasks/<int:task_id>', endpoint='delete_task', view_func=require_admin(controller.delete_task), methods=['DELETE'])
task_bp.add_url_rule('/tasks/search', endpoint='search_tasks', view_func=controller.search_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/stats', endpoint='task_stats', view_func=controller.task_stats, methods=['GET'])
