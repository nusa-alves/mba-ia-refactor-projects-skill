from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from config.constants import TASK_DONE_STATUS

class TaskRepository:
    @staticmethod
    def all():
        return Task.query.all()

    @staticmethod
    def list_with_relations():
        return Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()

    @staticmethod
    def get(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def for_user(user_id):
        return Task.query.filter_by(user_id=user_id).all()

    @staticmethod
    def search(query='', status='', priority=None, user_id=None):
        task_query = Task.query
        if query:
            task_query = task_query.filter(db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            ))
        if status:
            task_query = task_query.filter(Task.status == status)
        if priority is not None:
            task_query = task_query.filter(Task.priority == priority)
        if user_id is not None:
            task_query = task_query.filter(Task.user_id == user_id)
        return task_query.all()

    @staticmethod
    def count():
        return Task.query.count()

    @staticmethod
    def count_status(status):
        return Task.query.filter_by(status=status).count()

    @staticmethod
    def count_priority(priority):
        return Task.query.filter_by(priority=priority).count()

    @staticmethod
    def count_created_since(date):
        return Task.query.filter(Task.created_at >= date).count()

    @staticmethod
    def count_completed_since(date):
        return Task.query.filter(Task.status == TASK_DONE_STATUS, Task.updated_at >= date).count()

    @staticmethod
    def productivity_rows():
        return db.session.query(Task.user_id, Task.status).all()

    @staticmethod
    def category_counts():
        return dict(db.session.query(Task.category_id, func.count(Task.id))
                    .group_by(Task.category_id).all())

    @staticmethod
    def save(task):
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def delete(task):
        db.session.delete(task)
        db.session.commit()


class UserRepository:
    @staticmethod
    def all():
        return User.query.all()

    @staticmethod
    def list_with_tasks():
        return User.query.options(selectinload(User.tasks)).all()

    @staticmethod
    def get(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def count():
        return User.query.count()

    @staticmethod
    def save(user):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def delete_with_tasks(user):
        for task in Task.query.filter_by(user_id=user.id).all():
            db.session.delete(task)
        db.session.delete(user)
        db.session.commit()


class CategoryRepository:
    @staticmethod
    def count():
        return Category.query.count()

    @staticmethod
    def all():
        return Category.query.all()

    @staticmethod
    def get(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def save(category):
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def delete_detaching_tasks(category):
        Task.query.filter_by(category_id=category.id).update(
            {Task.category_id: None}, synchronize_session=False
        )
        db.session.delete(category)
        db.session.commit()
