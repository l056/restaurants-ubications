from flask import Flask, jsonify
import os
import redis
import logging
from werkzeug.exceptions import HTTPException
from src.models import db
from src.middleware.auth_middleware import token_required
from src.routes.routes import register_routes

logging.basicConfig(level=logging.DEBUG)

def create_app():
    """
    Crea y configura la aplicación Flask.
    Retorna:
        app (Flask): La aplicación Flask configurada.
    """
    app = Flask(__name__)

    # Configuración de la base de datos
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config['REDIS_HOST'] = os.getenv('REDIS_HOST')
    app.config['REDIS_PORT'] = int(os.getenv('REDIS_PORT'))

    # Inicialización de la base de datos
    db.init_app(app)

    # Configuración de Redis
    app.redis_client = redis.StrictRedis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=0,
        decode_responses=True
    )
    
    # Importar y registrar los middlewares
    app.token_required = token_required
    
    # Registrar rutas
    with app.app_context():
        register_routes(app)
        
     # Manejador de errores personalizado
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """ Maneja excepciones HTTP para devolver respuestas JSON. """
        response = jsonify({
            "error": e.description,
            "status_code": e.code
        })
        response.status_code = e.code
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        """ Maneja excepciones generales para devolver respuestas JSON. """
        response = jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        })
        response.status_code = 500
        return response
    
    return app