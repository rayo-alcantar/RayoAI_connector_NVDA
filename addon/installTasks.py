# RayoAI_connector_NVDA es un coplemento para compartírle imágenes y describirlas más rápidamente a RayoAI.
# Este archivo está cubierto por la Licencia Pública General de GNU.
# Consulta el archivo COPYING para más detalles.
# Última actualización 2025
# Derechos de autor (C) 2025 Ángel Alcántar <rayoalcantar@gmail.com>

import webbrowser

import wx
import gui
import globalVars
import addonHandler

addonHandler.initTranslation()


class donate:
    def open():
        # Directamente abrir la página de PayPal sin especificar el idioma.
        webbrowser.open("https://www.paypal.com/paypalme/rayoalcantar")

    def request():
        # Translators: The title of the dialog requesting donations from users.
        title = _("Por favor, dona")
        
        # Translators: The text of the donate dialog
        message = _("""RayoAI_connector_NVDA - complemento gratuito para NVDA.
Puedes hacer una donación a Ángel Alcántar para ayudar en el desarrollo futuro de este complemento.
¿Quieres hacer una donación ahora? Para la transacción, serás redirigido al sitio web de PayPal.""")
        
        name = addonHandler.getCodeAddon().manifest['summary']
        if gui.messageBox(message.format(name=name), title, style=wx.YES_NO|wx.ICON_QUESTION) == wx.YES:
            donate.open()
            return True
        return False

def onInstall():
    if not globalVars.appArgs.secure:
        donate.request()