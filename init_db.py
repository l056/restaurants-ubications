from app import create_app
from src.models import db

app = create_app()

# Crear el contexto de la aplicación
with app.app_context():
    # Crear todas las tablas en la base de datos
    db.create_all()

print("Tables created successfully")
