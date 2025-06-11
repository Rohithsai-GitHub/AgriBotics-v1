from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, email, password_hash=None):
        self.id = email  # Using email as ID
        self.email = email
        self.password_hash = password_hash

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @staticmethod
    def get(user_id):
        return users.get(user_id)

users = {}  # email -> User