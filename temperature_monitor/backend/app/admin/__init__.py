from flask import Blueprint

bp = Blueprint('admin', __name__)

from admin import routes
