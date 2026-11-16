from datetime import datetime, timedelta, timezone
from flask import jsonify, request
from models.category import Category
from models.repositories import TaskRepository as Tasks, UserRepository as Users, CategoryRepository as Categories
from controllers.validation import category_fields, json_object
from middlewares.errors import ApiError
from config.constants import REPORT_WINDOW_DAYS, TASK_STATUSES, TASK_PRIORITIES, TASK_PRIORITY_NAMES, DEFAULT_CATEGORY_COLOR

def summary_report():
    tasks = Tasks.all()
    overdue_tasks = [task for task in tasks if task.is_overdue()]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_start = now - timedelta(days=REPORT_WINDOW_DAYS)
    productivity = {}
    for user_id, status in Tasks.productivity_rows():
        total, completed = productivity.get(user_id, (0, 0))
        productivity[user_id] = (total + 1, completed + (status == 'done'))
    user_statistics = []
    for user in Users.all():
        total, completed = productivity.get(user.id, (0, 0))
        user_statistics.append({
            'user_id': user.id, 'user_name': user.name,
            'total_tasks': total, 'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total else 0,
        })
    report = {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Tasks.count(), 'total_users': Users.count(),
            'total_categories': Categories.count(),
        },
        'tasks_by_status': {status: Tasks.count_status(status) for status in TASK_STATUSES},
        'tasks_by_priority': {
            name: Tasks.count_priority(priority)
            for name, priority in zip(TASK_PRIORITY_NAMES, TASK_PRIORITIES)
        },
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [{
                'id': task.id, 'title': task.title, 'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            } for task in overdue_tasks],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Tasks.count_created_since(window_start),
            'tasks_completed_last_7_days': Tasks.count_completed_since(window_start),
        },
        'user_productivity': user_statistics,
    }
    return jsonify(report), 200

def user_report(user_id):
    user = Users.get(user_id)
    if not user:
        raise ApiError('Usu\u00e1rio n\u00e3o encontrado', 404)
    tasks = Tasks.for_user(user_id)
    counts = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1
    done = counts['done']
    total = len(tasks)
    report = {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'cancelled': counts['cancelled'],
            'overdue': sum(task.is_overdue() for task in tasks),
            'high_priority': sum(task.priority <= 2 for task in tasks),
            'completion_rate': round((done / total) * 100, 2) if total else 0,
        },
    }
    return jsonify(report), 200

def get_categories():
    counts = Tasks.category_counts()
    result = []
    for category in Categories.all():
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return jsonify(result), 200

def create_category():
    fields = category_fields(json_object(request))
    category = Category()
    category.name = fields['name']
    category.description = fields.get('description', '')
    category.color = fields.get('color', DEFAULT_CATEGORY_COLOR)
    Categories.save(category)
    return jsonify(category.to_dict()), 201

def update_category(cat_id):
    category = Categories.get(cat_id)
    if not category:
        raise ApiError('Categoria n\u00e3o encontrada', 404)
    fields = category_fields(json_object(request), partial=True)
    for field in ('name', 'description', 'color'):
        if field in fields:
            setattr(category, field, fields[field])
    Categories.save(category)
    return jsonify(category.to_dict()), 200

def delete_category(cat_id):
    category = Categories.get(cat_id)
    if not category:
        raise ApiError('Categoria n\u00e3o encontrada', 404)
    Categories.delete_detaching_tasks(category)
    return jsonify({'message': 'Categoria deletada'}), 200
