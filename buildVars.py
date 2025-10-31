# -*- coding: UTF-8 -*-
# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

def _(arg):
    return arg

addon_info = {
    "addon_name": "RayoAI_connector_for_NVDA",
    "addon_summary": _("RayoAI connector for NVDA"),
    "addon_description": _("""Complemento para enviarle imágenes a RayoAI más rápidamente."""),
    "addon_version": "2025.10.1",
    "addon_author": "Angel Alcántar <angelalcantar@rayoscompany.com>",
    "addon_url": "https://github.com/rayo-alcantar/RayoAI_connector_NVDA",
    "addon_sourceURL": "https://github.com/rayo-alcantar/RayoAI_connector_NVDA",
    "addon_docFileName": "readme.html",
    "addon_minimumNVDAVersion": 2023.1,
    "addon_lastTestedNVDAVersion": 2025.1,
    "addon_updateChannel": None,
    "addon_license": None,
    "addon_licenseURL": None,
}

import os

pythonSources = [
    os.path.join("addon", "globalPlugins", "*.py"),
    os.path.join("addon", "installTasks.py"),
]

i18nSources = pythonSources + ["buildVars.py"]

excludedFiles = []

baseLanguage = "es"

markdownExtensions = []

# ESTA ES LA PARTE QUE FALTABA PARA QUE SCONS NO TRUENE
brailleTables = []
