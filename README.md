# restaurants-ubications
Consulta de las ubicaciónes de los restaurantes en una ciudad o coordenadas

# Proceso para ejecución
- docker compose build
- docker compose up

# Servidor
Host = http://localhost
Port = 5000

# endpoints
- /register Metodo = POST 

Registro de un nuevo usuario

    - in
    {
    "username": "user",
    "email": "example@gmail.com",
    "password": "password"
    }

    - out
    {
    "message": "User registered successfully",
    "user_id": id_db
    }


- /login Metodo = POST

Login del usuario, no se puede loguearse nuevamente con el mismo usuario, tiempo de expiracion una hora o usando la ruta /logout
    - in
    {
    "email": "example@gmail.com",
    "password": "admin3"
    }

    - out
    {
    "access_token": "access_token",
    "message": "Login successful",
    "session_expiration": "Mon, 02 Sep 2024 01:35:31 GMT"
    }

- /restaurants Metodo = Get Autorización requerida BearerToken

params: city
o
params: lat,lon

Trae los restaurantes de una ciudad o coordenadas, se conecta a la api publica Nominatim, cuya url para peticiones es 
https://nominatim.openstreetmap.org/search?q='{city}'&format=json la cual permite trar las coordenadas de cualquier ciudad y usando la 
api publica Overpass, cuya url de request es http://overpass-api.de/api/interpreter con la query [out:json];
    node["amenity"="restaurant"](around:10000,{lat},{lon});
    out;

podemos obtener los restaurantes.

- /transactions Metodo = Get Autorización requerida BearerToken

Se puede obtener el registro en la base de datos de la transacciónes (busquedas de restaurantes) del usuario que usa el token de acceso

No es necesario usar params

 -out 
    {
        "transactions": [
            {
                "date": "2024-09-02T00:34:59.713517",
                "id": 9,
                "restaurants": [
                ]
            }
        ]
    }


- /logout Metodo POST Autorización requerida

    - out
    {
    "message": "Logout successful"
    }

los endpoints devuelven mensajes json para los errores. con su respectivo codigo descriptivo.

# Base de datos

- user
Contiene los valores 
id: llave primaria autoincremental
username (str): Nombre de usuario, único y no nulo.
email (str): Correo electrónico, único y no nulo.
password (str): Contraseña, no nula.

-transaction
Contiene los valores 
id (int): Clave primaria.
user_id (int): Clave foránea que referencia a 'user.id', no nula.
date (datetime): Fecha y hora de la transacción, no nula, con valor por defecto la fecha y hora actual.
restaurants (list[str]): Lista de nombres de restaurantes, puede ser nula.

