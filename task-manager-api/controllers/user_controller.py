import logging
from flask import current_app, jsonify, request
from itsdangerous import URLSafeTimedSerializer
from models.user import User
from models.repositories import TaskRepository as Tasks, UserRepository as Users
from controllers.validation import json_object, user_fields, credentials
from middlewares.errors import ApiError
from config.constants import DEFAULT_USER_ROLE

logger = logging.getLogger(__name__)

def get_users():
    response = []
    for user in Users.list_with_tasks():
        response.append({
            'id': user.id, 'name': user.name, 'email': user.email,
            'role': user.role, 'active': user.active,
            'created_at': str(user.created_at), 'task_count': len(user.tasks),
        })
    return jsonify(response), 200

def get_user(user_id):
    user = Users.get(user_id)
    if not user:
        raise ApiError('Usu\u00e1rio n\u00e3o encontrado', 404)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Tasks.for_user(user_id)]
    return jsonify(data), 200

def create_user():
    fields = user_fields(json_object(request), public=True)
    if Users.find_by_email(fields['email']):
        raise ApiError('Email j\u00e1 cadastrado', 409)
    user = User()
    user.name = fields['name']
    user.email = fields['email']
    user.set_password(fields['password'])
    user.role = DEFAULT_USER_ROLE
    Users.save(user)
    logger.info('User created: %s', user.id)
    return jsonify(user.to_dict()), 201

def update_user(user_id):
    user = Users.get(user_id)
    if not user:
        raise ApiError('Usu\u00e1rio n\u00e3o encontrado', 404)
    fields = user_fields(json_object(request), partial=True)
    if 'email' in fields:
        existing = Users.find_by_email(fields['email'])
        if existing and existing.id != user_id:
            raise ApiError('Email j\u00e1 cadastrado', 409)
    for field in ('name', 'email', 'role', 'active'):
        if field in fields:
            setattr(user, field, fields[field])
    if 'password' in fields:
        user.set_password(fields['password'])
    Users.save(user)
    return jsonify(user.to_dict()), 200

def delete_user(user_id):
    user = Users.get(user_id)
    if not user:
        raise ApiError('Usu\u00e1rio n\u00e3o encontrado', 404)
    Users.delete_with_tasks(user)
    logger.info('User deleted: %s', user_id)
    return jsonify({'message': 'Usu\u00e1rio deletado com sucesso'}), 200

def get_user_tasks(user_id):
    if not Users.get(user_id):
        raise ApiError('Usu\u00e1rio n\u00e3o encontrado', 404)
    response = []
    for task in Tasks.for_user(user_id):
        response.append({
            'id': task.id, 'title': task.title, 'description': task.description,
            'status': task.status, 'priority': task.priority,
            'created_at': str(task.created_at),
            'due_date': str(task.due_date) if task.due_date else None,
            'overdue': task.is_overdue(),
        })
    return jsonify(response), 200

def login():
    data = json_object(request)
    email, password = credentials(data)
    user = Users.find_by_email(email)
    if not user or not user.check_password(password):
        raise ApiError('Credenciais inv\u00e1lidas', 401)
    if not user.active:
        raise ApiError('Usu\u00e1rio inativo', 403)
    Users.save(user)
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='task-manager-auth')
    token = serializer.dumps({'user_id': user.id, 'role': user.role})
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200
