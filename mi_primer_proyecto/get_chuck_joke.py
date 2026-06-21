import requests

def obtener_chiste_chuck():
    url = "https://api.chucknorris.io/jokes/random"
    try:
        respuesta = requests.get(url)
        # Comprobar si la solicitud fue exitosa (código 200)
        respuesta.raise_for_status()
        
        datos = respuesta.json()
        chiste = datos.get("value")
        return chiste
    except requests.exceptions.RequestException as e:
        return f"Error al conectar con la API: {e}"

if __name__ == "__main__":
    chiste = obtener_chiste_chuck()
    print("--- Chiste de Chuck Norris ---")
    print(chiste)
    print("------------------------------")
