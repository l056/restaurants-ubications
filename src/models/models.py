from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
import datetime

db = SQLAlchemy()

class User(db.Model):
    """
    Define el modelo de usuario.
    Atributos:
        id (int): Clave primaria.
        username (str): Nombre de usuario, único y no nulo.
        email (str): Correo electrónico, único y no nulo.
        password (str): Contraseña, no nula.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Transaction(db.Model):
    """
    Define el modelo de transacción.
    Atributos:
        id (int): Clave primaria.
        user_id (int): Clave foránea que referencia a 'user.id', no nula.
        date (datetime): Fecha y hora de la transacción, no nula, con valor por defecto la fecha y hora actual.
        restaurants (list[str]): Lista de nombres de restaurantes, puede ser nula.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    restaurants = db.Column(ARRAY(db.String), nullable=True)