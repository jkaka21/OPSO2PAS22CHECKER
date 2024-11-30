import asyncio
from collections import deque
from form_filler import completar_formulario

queue = deque()

async def start_queue_processor(bot, group_id):
    while True:
        if queue:
            task = queue.popleft()
            user_id, username, tarjeta, mes, anio, codigo, message = task.values()
            try:
                result = await completar_formulario(tarjeta, mes, anio, codigo)
                response = (
                    f"Checkeo {'Exitoso' if result else 'Fallido'}\n"
                    f"Tarjeta: {tarjeta}\n"
                    f"Usuario: @{username}"
                )
                bot.reply_to(message, response)
                bot.send_message(group_id, response)
            except Exception as e:
                bot.reply_to(message, f"Error en la verificación: {e}")
        await asyncio.sleep(1)

def add_to_queue(user_id, username, tarjeta, mes, anio, codigo, message):
    queue.append({
        "user_id": user_id,
        "username": username,
        "tarjeta": tarjeta,
        "mes": mes,
        "anio": anio,
        "codigo": codigo,
        "message": message
    })
