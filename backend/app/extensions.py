"""Extensiones de Flask inicializadas sin aplicación.

Se declaran aquí (y no en ``app/__init__.py``) para evitar importaciones
circulares: los modelos pueden hacer ``from app.extensions import db`` sin
provocar que el paquete se importe a sí mismo.
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
