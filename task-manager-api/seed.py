"""Populate local demo data atomically."""
import logging
from datetime import datetime, timedelta, timezone
from app import app, db
from models.task import Task
from models.user import User
from models.category import Category

logger = logging.getLogger(__name__)

def seed_data():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with app.app_context():
        with db.session.begin():
            Task.query.delete()
            User.query.delete()
            Category.query.delete()

            users = [
                User(name='Jo\u00e3o Silva', email='joao@email.com', role='admin'),
                User(name='Maria Santos', email='maria@email.com', role='user'),
                User(name='Pedro Oliveira', email='pedro@email.com', role='manager'),
            ]
            for user, password in zip(users, ('1234', 'abcd', 'pass')):
                user.set_password(password)
            db.session.add_all(users)
            db.session.flush()

            categories = [
                Category(name='Backend', description='Tarefas de backend', color='#3498db'),
                Category(name='Frontend', description='Tarefas de frontend', color='#2ecc71'),
                Category(name='DevOps', description='Tarefas de infraestrutura', color='#e74c3c'),
                Category(name='Bug', description='Corre\u00e7\u00e3o de bugs', color='#e67e22'),
            ]
            db.session.add_all(categories)
            db.session.flush()

            task_data = [
                ('Implementar autentica\u00e7\u00e3o JWT', 'Adicionar autentica\u00e7\u00e3o real com JWT', 'pending', 1, 0, 0, now-timedelta(days=3), None),
                ('Criar tela de login', 'Tela de login responsiva', 'in_progress', 2, 1, 1, now+timedelta(days=5), None),
                ('Configurar CI/CD', 'Pipeline com GitHub Actions', 'done', 2, 2, 2, None, 'devops,ci,github'),
                ('Corrigir bug no filtro de busca', 'Filtro n\u00e3o funciona com caracteres especiais', 'pending', 1, 0, 3, now-timedelta(days=1), None),
                ('Adicionar pagina\u00e7\u00e3o na API', 'Endpoints retornam todos os registros', 'pending', 3, 0, 0, now+timedelta(days=10), None),
                ('Escrever testes unit\u00e1rios', 'Cobertura m\u00ednima de 80%', 'pending', 2, 1, 0, None, None),
                ('Documentar API com Swagger', 'Gerar documenta\u00e7\u00e3o autom\u00e1tica', 'cancelled', 4, 2, 0, None, None),
                ('Refatorar models', 'Melhorar organiza\u00e7\u00e3o dos models', 'in_progress', 3, 1, 0, None, 'refactor,tech-debt'),
                ('Configurar monitoramento', 'Prometheus + Grafana', 'pending', 4, 2, 2, now+timedelta(days=20), None),
                ('Melhorar valida\u00e7\u00f5es de input', 'Usar marshmallow ou pydantic', 'pending', 3, 0, 0, None, 'improvement,validation'),
            ]
            tasks = [
                Task(title=title, description=description, status=status, priority=priority,
                     user_id=users[user_index].id, category_id=categories[category_index].id,
                     due_date=due_date, tags=tags)
                for title, description, status, priority, user_index, category_index, due_date, tags in task_data
            ]
            db.session.add_all(tasks)

        logger.info('Seed completed: %s users, %s categories, %s tasks',
                    User.query.count(), Category.query.count(), Task.query.count())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    seed_data()
