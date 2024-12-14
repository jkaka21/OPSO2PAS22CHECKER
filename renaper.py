import requests

API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6OTQyLCJyb2xlIjoyLCJpYXQiOjE3MzI4OTEyMTh9.ZJE93rqr5TzXlJ3Tz-On9Cj9AerPc9pxMNayONJ5BSo"
RENAPER_API_URL = "https://colmen-api.rgn.io/renaper/new"

def consultar_dni(dni, gender):
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"dni": dni, "gender": gender}

    try:
        response = requests.post(RENAPER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return {
            "id_tramite_principal": data.get("id_tramite_principal"),
            "id_tramite_tarjeta_reimpresa": data.get("id_tramite_tarjeta_reimpresa"),
            "ejemplar": data.get("ejemplar"),
            "fecha_vencimiento": data.get("fecha_vencimiento"),
            "fecha_emision": data.get("fecha_emision"),
            "apellido": data.get("apellido"),
            "nombres": data.get("nombres"),
            "fecha_nacimiento": data.get("fecha_nacimiento"),
            "id_ciudadano": data.get("id_ciudadano"),
            "cuil": data.get("cuil"),
            "calle": data.get("calle"),
            "numero": data.get("numero"),
            "piso": data.get("piso"),
            "departamento": data.get("departamento"),
            "codigo_postal": data.get("codigo_postal"),
            "barrio": data.get("barrio"),
            "monoblock": data.get("monoblock"),
            "ciudad": data.get("ciudad"),
            "municipio": data.get("municipio"),
            "provincia": data.get("provincia"),
            "pais": data.get("pais"),
            "codigo_fallecido": data.get("codigo_fallecido"),
            "mensaje_fallecido": data.get("mensaje_fallecido"),
            "origen_fallecido": data.get("origen_fallecido"),
            "fecha_fallecido": data.get("fecha_fallecido"),
            "foto": data.get("foto"),  # Foto en base64
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al conectar con la API del RENAPER: {e}"}
