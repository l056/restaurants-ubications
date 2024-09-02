import requests
import logging

logging.basicConfig(level=logging.DEBUG)

def get_coords_by_city(city):
    """
    Obtiene las coordenadas (latitud y longitud) de una ciudad utilizando la API de Nominatim.
    Parámetros:
        city (str): Nombre de la ciudad.
    Retorna:
        tuple: Una tupla con la latitud y longitud de la ciudad, o (None, None) si no se encuentran datos.
    """
    response = requests.get(f"https://nominatim.openstreetmap.org/search?q='{city}'&format=json")
    data = response.json()
    if not data:
        return None, None
    return data[0]['lat'], data[0]['lon']

def get_restaurants_by_city(city):
    """
    Obtiene una lista de restaurantes en una ciudad específica.
    Parámetros:
        city (str): Nombre de la ciudad.
    Retorna:
        list: Una lista de diccionarios con información de los restaurantes.
    """
    lat, lon = get_coords_by_city(city)
    if not lat or not lon:
        return []

    return get_restaurants_by_coords(lat, lon)

def get_restaurants_by_coords(lat, lon):
    """
    Obtiene una lista de restaurantes cercanos a unas coordenadas específicas utilizando la API de Overpass.
    Parámetros:
        lat (float): Latitud.
        lon (float): Longitud.
    Retorna:
        list: Una lista de diccionarios con información de los restaurantes.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    node["amenity"="restaurant"](around:10000,{lat},{lon});
    out;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    restaurants = []
    for element in data['elements']:
        if 'tags' in element and 'name' in element['tags']:
            restaurants.append({
                'name': element['tags']['name'],
                'lat': element['lat'],
                'lon': element['lon']
            })
    return restaurants
