import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

ACCESS_FILE = "access_list.json"

def load_access_list():
    try:
        with open(ACCESS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_access_list(access_list):
    with open(ACCESS_FILE, "w") as file:
        json.dump(access_list, file)

def check_access(username):
    access_list = load_access_list()
    if username not in access_list:
        return False
    expiry_date = access_list[username].get("expiry_date")
    if not expiry_date:
        return True
    return datetime.now() <= datetime.strptime(expiry_date, "%Y-%m-%d")

def grant_access(username, duration):
    access_list = load_access_list()
    if duration == "lifetime":
        expiry_date = None
    elif duration.endswith("m"):
        months = int(duration[:-1])
        expiry_date = (datetime.now() + relativedelta(months=months)).strftime("%Y-%m-%d")
    elif duration.endswith("d"):
        days = int(duration[:-1])
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    else:
        return "Duración inválida. Usa '1m', '30d', 'lifetime', etc."

    access_list[username] = {"expiry_date": expiry_date}
    save_access_list(access_list)
    return f"Acceso otorgado a @{username} {'de por vida' if not expiry_date else f'hasta el {expiry_date}'}."

def revoke_access(username):
    access_list = load_access_list()
    if username not in access_list:
        return f"El usuario @{username} no está en la lista."
    del access_list[username]
    save_access_list(access_list)
    return f"Acceso revocado a @{username}."
