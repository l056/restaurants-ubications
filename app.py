from flask import Flask, request, jsonify, abort
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.security import generate_password_hash, check_password_hash
from src.middleware.auth_middleware import token_required
from src.services.restaurant_service import *
import jwt
import datetime
import logging
import redis
from werkzeug.exceptions import HTTPException
from flask import current_app
from src.models import db, User, Transaction
from src.middleware.auth_middleware import token_required
import re

logging.basicConfig(level=logging.DEBUG)
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

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


app = create_app()


# Rutas
@app.route("/register", methods=["POST"])
def register():
    """
    Registra un nuevo usuario.
    Retorna:
        response (json): Mensaje de éxito y el ID del usuario registrado.
    """
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        abort(400, "Missing required fields")

    # Validar formato del correo electrónico
    if not re.match(EMAIL_REGEX, email):
        abort(400, "Invalid email format")
        
    hashed_password = generate_password_hash(password, method="sha256")

    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, "User already exists")

    return jsonify(message="User registered successfully", user_id=new_user.id), 201


@app.route("/login", methods=["POST"])
def login():
    """
    Autentica a un usuario y genera un token JWT.
    Retorna:
        response (json): Mensaje de éxito, token de acceso y tiempo de expiración de la sesión.
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        abort(400, "Missing required fields")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        abort(401, "Invalid credentials")

    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    logging.info(f"User {user.id} logged in successfully")
    existing_token = current_app.redis_client.get(user.id)
    if existing_token:
        return jsonify(message="User is already logged in. Please log out before logging in again."), 403
    current_app.redis_client.setex(str(user.id), datetime.timedelta(hours=1), token)
    
    return jsonify(message="Login successful", access_token=token, session_expiration=datetime.datetime.utcnow() + datetime.timedelta(hours=1))


@app.route("/restaurants", methods=["GET"])
@token_required
def get_restaurants():
    """
    Obtiene una lista de restaurantes basados en la ciudad o coordenadas proporcionadas.
    Retorna:
        response (json): Lista de restaurantes.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        abort(401, "Authorization header missing")
    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        abort(401, "Token expired")
    except jwt.InvalidTokenError:
        abort(401, "Invalid token")

    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    try:
        if city:
            restaurants_all = get_restaurants_by_city(city)
                
        elif lat and lon:
            restaurants_all = get_restaurants_by_coords(lat, lon)

        else:
            abort(400, "Please provide a city or coordinates.")
            
        restaurants = [r["name"] for r in restaurants_all]
        new_transaction = Transaction(
            user_id=jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["user_id"],
            restaurants = restaurants,
            date = datetime.datetime.utcnow()
        )
        db.session.add(new_transaction)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    except Exception as e:
        logging.error("Failed to get restaurants ", e)
        return jsonify({"message": "Failed to get restaurants"}), 500

    return jsonify(restaurants=restaurants)


@app.route("/transactions", methods=["GET"])
@token_required
def get_transactions():
    """
    Obtiene una lista de transacciones del usuario autenticado.
    Retorna:
        response (json): Lista de transacciones.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        abort(401, "Authorization header missing")
    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        abort(401, "Token expired")
    except jwt.InvalidTokenError:
        abort(401, "Invalid token")

    # Filtra transacciones del usuario autenticado
    user_id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])[
        "user_id"
    ]
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    result = [
        {
            "id": t.id,
            "date": t.date.isoformat(),
            "restaurants": t.restaurants,
        }
        for t in transactions
    ]

    return jsonify(transactions=result)


@app.route("/logout", methods=["POST"])
@token_required
def logout():
    """
    Cierra la sesión del usuario invalidando el token JWT.
    Retorna:
        response (json): Mensaje de éxito.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        app.logger.warning("Authorization header missing")
        abort(401, "Authorization header missing")
    
    token = auth_header.split(" ")[1]
    
    try:
        decoded_token = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = str(decoded_token["user_id"])
    except jwt.ExpiredSignatureError:
        app.logger.warning(f"Token expired for user_id: {user_id}")
        abort(401, "Token expired")
    except jwt.InvalidTokenError:
        app.logger.warning("Invalid token")
        abort(401, "Invalid token")

    logging.info(f"Invalidating token for user_id: {user_id}")
    # Eliminar el token de Redis usando el user_id
    if current_app.redis_client.delete(user_id):
        app.logger.info(f"Token for user_id: {user_id} invalidated")
    else:
        app.logger.warning(f"Failed to invalidate token for user_id: {user_id}")

    return jsonify(message="Logout successful")
