import logging
from datetime import datetime, timezone
from flask import jsonify, request
from models.task import Task
from models.repositories import TaskRepository as Tasks, UserRepository as Users, CategoryRepository as Categories
from controllers.validation import json_object, task_fields
from middlewares.errors import ApiError

logger = logging.getLogger(__name__)

def get_tasks():
    response = []
    for task in Tasks.list_with_relations():
        data = task.to_dict()
        data.update({
            'overdue': task.is_overdue(),
            'user_name': task.user.name if task.user else None,
            'category_name': task.category.name if task.category else None,
        })
        response.append(data)
    return jsonify(response), 200

def get_task(task_id):
    task = Tasks.get(task_id)
    if not task:
        raise ApiError('Task n\u00e3o encontrada', 404)
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return jsonify(data), 200

def create_task():
    fields = task_fields(json_object(request))
    for field, repository, message in (
        ('user_id', Users, 'Usu\u00e1rio n\u00e3o encontrado'),
        ('category_id', Categories, 'Categoria n\u00e3o encontrada'),
    ):
        if fields.get(field) and not repository.get(fields[field]):
            raise ApiError(message, 404)
    task = Task()
    task.title = fields['title']
    task.description = fields.get('description', '')
    task.status = fields['status']
    task.priority = fields['priority']
    task.user_id = fields.get('user_id')
    task.category_id = fields.get('category_id')
    if fields.get('due_date'):
        task.due_date = datetime.strptime(fields['due_date'], '%Y-%m-%d')
    task.tags = fields.get('tags')
    Tasks.save(task)
    logger.info('Task created: %s', task.id)
    return jsonify(task.to_dict()), 201

def update_task(task_id):
    task = Tasks.get(task_id)
    if not task:
        raise ApiError('Task n\u00e3o encontrada', 404)
    fields = task_fields(json_object(request), partial=True)
    if 'user_id' in fields and fields['user_id'] and not Users.get(fields['user_id']):
        raise ApiError('Usu\u00e1rio n\u00e3o encontrado', 404)
    if 'category_id' in fields and fields['category_id'] and not Categories.get(fields['category_id']):
        raise ApiError('Categoria n\u00e3o encontrada', 404)
    for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id', 'tags'):
        if field in fields:
            setattr(task, field, fields[field])
    if 'due_date' in fields:
        task.due_date = datetime.strptime(fields['due_date'], '%Y-%m-%d') if fields['due_date'] else None
    task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    Tasks.save(task)
    logger.info('Task updated: %s', task.id)
    return jsonify(task.to_dict()), 200

def delete_task(task_id):
    task = Tasks.get(task_id)
    if not task:
        raise ApiError('Task n\u00e3o encontrada', 404)
    Tasks.delete(task)
    logger.info('Task deleted: %s', task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200

def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority_value = request.args.get('priority', '')
    user_id_value = request.args.get('user_id', '')
    try:
        priority = int(priority_value) if priority_value else None
        user_id = int(user_id_value) if user_id_value else None
    except ValueError as error:
        raise ApiError('Filtros num\u00e9ricos inv\u00e1lidos', 400) from error
    return jsonify([task.to_dict() for task in Tasks.search(query, status, priority, user_id)]), 200

def task_stats():
    total = Tasks.count()
    done = Tasks.count_status('done')
    stats = {
        'total': total,
        'pending': Tasks.count_status('pending'),
        'in_progress': Tasks.count_status('in_progress'),
        'done': done,
        'cancelled': Tasks.count_status('cancelled'),
        'overdue': sum(task.is_overdue() for task in Tasks.all()),
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
    return jsonify(stats), 200
