import os
import telebot
import asyncio
from dotenv import load_dotenv
from access_manager import check_access, grant_access, revoke_access
from queue_processor import add_to_queue, start_queue_processor

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = telebot.TeleBot(API_TOKEN)

asyncio.create_task(start_queue_processor(bot, GROUP_ID))

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, (
        "¡Hola! 👋 Soy tu asistente virtual. 🤖\n\n"
        "Uso: /check cc|mes|año|cvv para verificar tarjetas.\n"
    ))

@bot.message_handler(commands=['acceso'])
def handle_acceso(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "No tienes permiso para usar este comando.")
        return

    args = message.text.split(" ", 2)
    if len(args) < 3:
        bot.reply_to(message, "Formato incorrecto. Usa: /acceso @usuario duración")
        return

    username = args[1][1:]
    duration = args[2]
    result = grant_access(username, duration)
    bot.reply_to(message, result)

@bot.message_handler(commands=['revoque'])
def handle_revoque(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "No tienes permiso para usar este comando.")
        return

    args = message.text.split(" ", 1)
    if len(args) != 2:
        bot.reply_to(message, "Formato incorrecto. Usa: /revoque @usuario")
        return

    username = args[1][1:]
    result = revoke_access(username)
    bot.reply_to(message, result)

@bot.message_handler(commands=['check'])
def handle_check(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    args = message.text.split(" ", 1)

    if len(args) != 2 or "|" not in args[1]:
        bot.reply_to(message, "Formato incorrecto. Usa: /check cc|mes|año|cvv")
        return

    if not check_access(username):
        bot.reply_to(message, "No tienes acceso. Contacta al administrador.")
        return

    tarjeta, mes, anio, codigo = args[1].split("|")
    if len(tarjeta) != 16 or not tarjeta.isdigit():
        bot.reply_to(message, "La tarjeta debe tener 16 dígitos.")
        return
    if not mes.isdigit() or int(mes) < 1 or int(mes) > 12:
        bot.reply_to(message, "Mes inválido.")
        return
    if not anio.isdigit() or int(anio) < 24:
        bot.reply_to(message, "Año inválido.")
        return
    if len(codigo) not in [3, 4] or not codigo.isdigit():
        bot.reply_to(message, "CVV inválido.")
        return

    add_to_queue(user_id, username, tarjeta, mes, anio, codigo, message)
    bot.reply_to(message, "Procesando tu solicitud. Por favor espera...")

if __name__ == "__main__":
    print("Bot iniciado.")
    bot.infinity_polling()
