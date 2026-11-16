from database import db
from datetime import datetime, timezone
import hashlib
import hmac
from werkzeug.security import generate_password_hash, check_password_hash
from config.constants import DEFAULT_USER_ROLE

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_USER_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if self.password.startswith(("scrypt:", "pbkdf2:")):
            return check_password_hash(self.password, password)
        legacy_hash = hashlib.md5(password.encode()).hexdigest()
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(password)
            return True
        return False

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False
