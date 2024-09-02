from functools import wraps
import jwt
from flask import request, abort, current_app
import redis

def token_required(f):
    """
    Decorador para verificar la validez del token JWT en las solicitudes.
    Parámetros:
        f (func): La función a decorar.
    Retorna:
        func: La función decorada.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        """
        Función decorada que verifica el token JWT.
        Parámetros:
            *args: Argumentos posicionales.
            **kwargs: Argumentos con nombre.
        Retorna:
            func: La función original si el token es válido.
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            abort(401, 'Authorization header missing')

        token = auth_header.split(" ")[1]
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data.get('user_id')
            
            # Verificar si el token ha sido invalidado en Redis
            redis_client = current_app.redis_client
            if redis_client.get(user_id) is None:
                abort(401, 'Token invalid or expired')
            
        except jwt.ExpiredSignatureError:
            abort(401, 'Token expired')
        except jwt.InvalidTokenError:
            abort(401, 'Invalid token')
        except jwt.InvalidSignatureError:
            abort(401, 'Invalid token signature')
        except jwt.DecodeError:
            abort(401, 'Failed to decode token')
        except Exception as e:
            # Manejar cualquier otro error
            if '401' in str(e):
                abort(401, str(e))
            abort(500, f'An unexpected error occurred: {str(e)}')

        return f(*args, **kwargs)
    return decorated
