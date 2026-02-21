from models import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import hmac

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        """ Hash and set the password. """
        self.password_hash = generate_password_hash(password)  # No need to specify 'sha256'

    def check_password(self, password):
        """ Verify the password against the stored hash. """
        return check_password_hash(self.password_hash, password)


