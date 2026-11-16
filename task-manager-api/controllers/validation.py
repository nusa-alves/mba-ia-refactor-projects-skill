import re
from datetime import datetime
from middlewares.errors import ApiError
from config.constants import (
    DEFAULT_TASK_PRIORITY, DEFAULT_TASK_STATUS, DEFAULT_USER_ROLE, MAX_TASK_TITLE_LENGTH, MIN_PASSWORD_LENGTH,
    MIN_TASK_TITLE_LENGTH, MIN_TASK_PRIORITY, MAX_TASK_PRIORITY, TASK_PRIORITIES, TASK_STATUSES, USER_ROLES,
)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

def json_object(request):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError('Dados inv\u00e1lidos', 400)
    return payload

def task_fields(payload, partial=False):
    if not partial and not payload.get('title'):
        raise ApiError('T\u00edtulo \u00e9 obrigat\u00f3rio', 400)
    if 'title' in payload:
        title = payload['title']
        if not isinstance(title, str):
            raise ApiError('T\u00edtulo inv\u00e1lido', 400)
        if len(title) < MIN_TASK_TITLE_LENGTH:
            raise ApiError('T\u00edtulo muito curto', 400)
        if len(title) > MAX_TASK_TITLE_LENGTH:
            raise ApiError('T\u00edtulo muito longo', 400)
    if 'status' in payload and payload['status'] not in TASK_STATUSES:
        raise ApiError('Status inv\u00e1lido', 400)
    if 'priority' in payload:
        priority = payload['priority']
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ApiError('Prioridade deve ser um n\u00famero inteiro', 400)
        if priority not in TASK_PRIORITIES:
            raise ApiError('Prioridade deve ser entre 1 e 5', 400)
    for field in ('user_id', 'category_id'):
        if field in payload and payload[field] is not None:
            if not isinstance(payload[field], int) or isinstance(payload[field], bool) or payload[field] < 1:
                raise ApiError(f'{field} inv\u00e1lido', 400)
    if 'due_date' in payload and payload['due_date']:
        if not isinstance(payload['due_date'], str):
            raise ApiError('Formato de data inv\u00e1lido. Use YYYY-MM-DD', 400)
        try:
            datetime.strptime(payload['due_date'], '%Y-%m-%d')
        except ValueError as error:
            raise ApiError('Formato de data inv\u00e1lido. Use YYYY-MM-DD', 400) from error
    if 'tags' in payload and not isinstance(payload['tags'], (str, list)):
        raise ApiError('Tags inv\u00e1lidas', 400)
    if isinstance(payload.get('tags'), list) and not all(isinstance(tag, str) for tag in payload['tags']):
        raise ApiError('Tags inv\u00e1lidas', 400)
    fields = dict(payload)
    if not partial:
        fields.setdefault('priority', DEFAULT_TASK_PRIORITY)
        fields.setdefault('status', DEFAULT_TASK_STATUS)
    if isinstance(fields.get('tags'), list):
        fields['tags'] = ','.join(fields['tags'])
    return fields

def user_fields(payload, partial=False, public=False):
    required = ('name', 'email', 'password')
    if not partial:
        for field in required:
            if not payload.get(field):
                labels = {'name': 'Nome', 'email': 'Email', 'password': 'Senha'}
                raise ApiError(f'{labels[field]} \u00e9 obrigat\u00f3rio', 400)
    for field in ('name', 'email', 'password'):
        if field in payload and not isinstance(payload[field], str):
            raise ApiError(f'{field} inv\u00e1lido', 400)
    if 'email' in payload and not EMAIL_PATTERN.match(payload['email']):
        raise ApiError('Email inv\u00e1lido', 400)
    if 'password' in payload and len(payload['password']) < MIN_PASSWORD_LENGTH:
        message = 'Senha deve ter no m\u00ednimo 4 caracteres' if not partial else 'Senha muito curta'
        raise ApiError(message, 400)
    fields = dict(payload)
    if public:
        fields.pop('role', None)
        fields['role'] = DEFAULT_USER_ROLE
    elif 'role' in fields and fields['role'] not in USER_ROLES:
        raise ApiError('Role inv\u00e1lido', 400)
    if 'active' in fields and not isinstance(fields['active'], bool):
        raise ApiError('Status active inv\u00e1lido', 400)
    return fields

def category_fields(payload, partial=False):
    if not partial and not payload.get('name'):
        raise ApiError('Nome \u00e9 obrigat\u00f3rio', 400)
    for field in ('name', 'description', 'color'):
        if field in payload and not isinstance(payload[field], str):
            raise ApiError(f'{field} inv\u00e1lido', 400)
    return dict(payload)

def credentials(payload):
    email = payload.get('email')
    password = payload.get('password')
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email) or not isinstance(password, str) or not password:
        raise ApiError('Email e senha s\u00e3o obrigat\u00f3rios', 400)
    return email, password
