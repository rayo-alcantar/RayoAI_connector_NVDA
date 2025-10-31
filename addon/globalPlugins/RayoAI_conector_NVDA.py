#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2025 Ángel Alcantar

"""NVDA connector for RayoAI (Windows).

This NVDA global plugin allows sending the currently focused object image
or an image URL (downloaded) to the RayoAI desktop app via its local IPC.


Security considerations:
- Only connects to 127.0.0.1 on a configurable local port.
- Sends only file paths (no raw pixels over the wire).
"""

from __future__ import annotations

import socket
import json
import os
import tempfile
import time
import ctypes
from ctypes import wintypes
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import addonHandler  # type: ignore
import api  # type: ignore
import config  # type: ignore
import controlTypes  # type: ignore
import globalPluginHandler  # type: ignore
import gui  # type: ignore
import ui  # type: ignore
from scriptHandler import script  # type: ignore


addonHandler.initTranslation()


# Settings: RayoAI IPC port (JSON over TCP, localhost only)
confSpecs = {"port": "integer(min=1, max=65535, default=16180)"}
config.conf.spec["rayoai"] = confSpecs
conf = config.conf["rayoai"]


def _send_ipc(payload: dict) -> bool:
	"""Send a JSON payload to the RayoAI local IPC.

	Returns True if we could connect and send without error; False otherwise.
	"""
	addr = ("127.0.0.1", int(conf.get("port", 16180)))
	try:
		data = json.dumps(payload).encode("utf-8")
		with socket.create_connection(addr, timeout=1.5) as s:
			s.sendall(data)
		return True
	except Exception:
		return False


def _send_open_path(path: str) -> bool:
	path = os.path.abspath(path)
	return _send_ipc({"cmd": "open", "path": path})


def _send_focus() -> bool:
	return _send_ipc({"cmd": "focus"})


# ---- Windows GDI screen capture helpers (no external deps) ----

# GDI constants
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = wintypes.INT

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
gdi32.BitBlt.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, wintypes.LPVOID, wintypes.LPVOID, wintypes.UINT]
gdi32.GetDIBits.restype = ctypes.c_int


class BITMAPINFOHEADER(ctypes.Structure):
	_fields_ = [
		("biSize", wintypes.DWORD),
		("biWidth", ctypes.c_long),
		("biHeight", ctypes.c_long),
		("biPlanes", wintypes.WORD),
		("biBitCount", wintypes.WORD),
		("biCompression", wintypes.DWORD),
		("biSizeImage", wintypes.DWORD),
		("biXPelsPerMeter", ctypes.c_long),
		("biYPelsPerMeter", ctypes.c_long),
		("biClrUsed", wintypes.DWORD),
		("biClrImportant", wintypes.DWORD),
	]


class BITMAPFILEHEADER(ctypes.Structure):
	_pack_ = 1
	_fields_ = [
		("bfType", wintypes.WORD),
		("bfSize", wintypes.DWORD),
		("bfReserved1", wintypes.WORD),
		("bfReserved2", wintypes.WORD),
		("bfOffBits", wintypes.DWORD),
	]


def _capture_rect_to_bmp(left: int, top: int, right: int, bottom: int) -> str | None:
	"""Capture screen rectangle to a temp .bmp file and return its path.

	Returns None on failure.
	"""
	width = max(0, int(right) - int(left))
	height = max(0, int(bottom) - int(top))
	if width <= 2 or height <= 2:
		return None

	src_dc = user32.GetDC(0)
	if not src_dc:
		return None
	mem_dc = gdi32.CreateCompatibleDC(src_dc)
	if not mem_dc:
		user32.ReleaseDC(0, src_dc)
		return None
	hbm = gdi32.CreateCompatibleBitmap(src_dc, width, height)
	if not hbm:
		gdi32.DeleteDC(mem_dc)
		user32.ReleaseDC(0, src_dc)
		return None
	old_obj = gdi32.SelectObject(mem_dc, hbm)
	try:
		if not gdi32.BitBlt(mem_dc, 0, 0, width, height, src_dc, int(left), int(top), SRCCOPY):
			return None

		# Prepare 24-bit DIB
		bi = BITMAPINFOHEADER()
		bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
		bi.biWidth = width
		bi.biHeight = height  # bottom-up DIB
		bi.biPlanes = 1
		bi.biBitCount = 24
		bi.biCompression = 0  # BI_RGB
		bi.biSizeImage = 0
		bi.biXPelsPerMeter = 0
		bi.biYPelsPerMeter = 0
		bi.biClrUsed = 0
		bi.biClrImportant = 0

		# Row size aligned to 4 bytes
		row_size = ((bi.biBitCount * width + 31) // 32) * 4
		image_size = row_size * height
		pixel_data = (ctypes.c_ubyte * image_size)()

		# Allocate BITMAPINFO with header only
		class _BMI(ctypes.Structure):
			_fields_ = [("bmiHeader", BITMAPINFOHEADER)]

		bmi = _BMI()
		ctypes.memmove(ctypes.addressof(bmi.bmiHeader), ctypes.addressof(bi), ctypes.sizeof(BITMAPINFOHEADER))

		# GetDIBits to fill pixel_data
		got = gdi32.GetDIBits(mem_dc, hbm, 0, height, ctypes.byref(pixel_data), ctypes.byref(bmi), DIB_RGB_COLORS)
		if got != height:
			return None

		# Build BMP file
		bf = BITMAPFILEHEADER()
		bf.bfType = 0x4D42  # 'BM'
		bf_off_bits = ctypes.sizeof(BITMAPFILEHEADER) + ctypes.sizeof(BITMAPINFOHEADER)
		bf.bfOffBits = bf_off_bits
		bf.bfSize = bf_off_bits + image_size
		bf.bfReserved1 = 0
		bf.bfReserved2 = 0

		fd, tmp_path = tempfile.mkstemp(prefix="rayoai_nvda_", suffix=".bmp")
		os.close(fd)
		with open(tmp_path, "wb") as f:
			f.write(ctypes.string_at(ctypes.addressof(bf), ctypes.sizeof(BITMAPFILEHEADER)))
			f.write(ctypes.string_at(ctypes.addressof(bmi.bmiHeader), ctypes.sizeof(BITMAPINFOHEADER)))
			f.write(bytearray(pixel_data))
		return tmp_path
	except Exception:
		return None
	finally:
		gdi32.SelectObject(mem_dc, old_obj)
		gdi32.DeleteObject(hbm)
		gdi32.DeleteDC(mem_dc)
		user32.ReleaseDC(0, src_dc)


def _download_image_to_temp(url: str, name_hint: str | None = None) -> str | None:
	"""Download image from URL to a temp file and return its path.

	Tries to infer extension from URL or content-type. Returns None on failure.
	"""
	try:
		ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NVDA-RayoAI/1.0"
		req = Request(url, headers={"User-Agent": ua})
		with urlopen(req, timeout=7.5) as resp:
			data = resp.read()
			ctype = resp.headers.get("Content-Type", "").lower()
	except Exception:
		return None

	# Guess extension
	ext = None
	parsed = urlparse(url)
	base = os.path.basename(parsed.path or "")
	if "." in base:
		ext = os.path.splitext(base)[1].lower()
	if not ext:
		if "image/png" in ctype:
			ext = ".png"
		elif "image/jpeg" in ctype or "image/jpg" in ctype:
			ext = ".jpg"
		elif "image/bmp" in ctype:
			ext = ".bmp"
		elif "image/gif" in ctype:
			ext = ".gif"
		else:
			ext = ".png"

	prefix = "rayoai_url_"
	if name_hint:
		try:
			safe = "".join(ch for ch in name_hint if ch.isalnum() or ch in ("-", "_"))[:40]
			if safe:
				prefix = f"rayoai_{safe}_"
		except Exception:
			pass

	fd, tmp_path = tempfile.mkstemp(prefix=prefix, suffix=ext)
	os.close(fd)
	try:
		with open(tmp_path, "wb") as f:
			f.write(data)
		return tmp_path
	except Exception:
		try:
			os.remove(tmp_path)
		except Exception:
			pass
		return None


class SettingsDlg(gui.settingsDialogs.SettingsPanel):
	"""NVDA settings panel for the RayoAI connector."""

	title = "RayoAI Connector"

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.port = sHelper.addLabeledControl(
			# Translators: The port is specified to make the connection with rayoAI.
			_("puerto para conectarse a RayoAI:"),
			gui.nvdaControls.SelectOnFocusSpinCtrl,
			min=1,
			max=65535,
			initial=conf["port"],
		)

	def onSave(self):
		conf["port"] = self.port.GetValue()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	"""NVDA Global plugin for the RayoAI connector."""

	scriptCategory = "RayoAI Connector"

	def __init__(self):
		super().__init__()
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SettingsDlg)
		except Exception:
			pass

	def terminate(self):
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SettingsDlg)
		except Exception:
			pass
		super().terminate()

	def _checkScreenCurtain(self) -> bool:
		"""Warn if NVDA screen curtain is active."""
		try:
			import vision  # type: ignore
			from visionEnhancementProviders.screenCurtain import ScreenCurtainProvider  # type: ignore

			screenCurtainId = ScreenCurtainProvider.getSettings().getId()
			info = vision.handler.getProviderInfo(screenCurtainId)
			running = bool(vision.handler.getProviderInstance(info))
			if running:
				# Translators: a prompt is given to disable the screen curtain before taking a screenshot.
				ui.message(_("Desactive la cortina de pantalla antes de tomar una captura de pantalla."))
			return running
		except Exception:
			return False

	def _get_base_url(self):
		obj = api.getNavigatorObject()
		url = None
		while obj:
			obj = obj.parent
			if not obj:
				break
			if obj.role != controlTypes.Role.DOCUMENT:
				continue
			try:
				url = obj.IAccessibleObject.accValue(obj.IAccessibleChildID)
			except Exception:
				url = None
			if url and isinstance(url, str) and url.startswith("http"):
				try:
					url = "/".join(url.split("/", 3)[:3])
				except Exception:
					pass
				break
		return url

	@staticmethod
	def _focus_rayo():
		_send_focus()

	@script(
		gesture="kb:nvda+shift+k",
			# translators: Describes the action of a keyboard gesture to capture the object browser, take a screenshot, and send to RayoAI.
		description=_("Capturar el elemento del navegador de objetos y enviarlo a RayoAI"),
	)
	def script_grabObject(self, gesture):
		if self._checkScreenCurtain():
			return
		nav = api.getNavigatorObject()
		name = getattr(nav, "name", None)
		try:
			nav.scrollIntoView()
		except BaseException:
			pass
		try:
			left, top, width, height = nav.location
		except Exception:
			# Translators: Message to announce that the object navigator position cannot be found.
			ui.message(_("No se puede obtener la ubicación del objeto."))
			return
		right = int(left) + int(width)
		bottom = int(top) + int(height)

		bmp_path = _capture_rect_to_bmp(int(left), int(top), right, bottom)
		if not bmp_path:
			# Translators: Message to announce that you cannot take a photo of the object navigator.
			ui.message(_("No se puede capturar la imagen del navegador de objetos."))
			return

		ok = _send_open_path(bmp_path)
		if not ok:
			# Translators: Message to indicate that the image could not be sent to RayoAI, the question is asked in the form of a suggestion for the user to verify if the program is open and working.
			ui.message(_("No se puede enviar la imagen a RayoAI. ¿Está abierto y funcionando?"))
			return
		if name:
			# translators: The image is reported to have been sent to rayoAI.
			ui.message(_("Imagen del objeto enviada a RayoAI: %s") % name)
		else:
			# translators: The image is reported to have been sent to rayoAI.
			ui.message(_("Imagen del navegador de objetos enviada a RayoAI"))

	@script(
		gesture="kb:nvda+shift+l",
			# Translators: It is explained that this key shortcut will download the SRC image and send it to RayoAI.
		description=_("Descarga la imagen actual src y envíala a RayoAI"),
	)
	def script_sendURL(self, gesture):
		nav = api.getNavigatorObject()
		name = getattr(nav, "name", None)
		try:
			attrs = getattr(nav, "IA2Attributes", None)
		except Exception:
			attrs = None
		if not attrs or "src" not in attrs:
			# Translators: It reports that the SRC font was not found, and asks the user a question in the form of a hint about whether the font is an image.
			ui.message(_("src no encontrado. ¿Es esta una imagen?"))
			return

		src = attrs.get("src")
		if isinstance(src, str) and src.startswith("/"):
			base = self._get_base_url()
			if not base:
				# translators: It is reported that the base url could not be found.
				ui.message(_("No se puede recuperar la URL base"))
				return
			src = base + src

		if not isinstance(src, str) or not src.lower().startswith("http"):
			# Translators: It is reported that the SRC font is not compatible for download.
			ui.message(_("Src no compatible para descargar."))
			return

		tmp = _download_image_to_temp(src, name_hint=name if isinstance(name, str) else None)
		if not tmp:
			ui.message(_("No se puede descargar la imagen."))
			return

		ok = _send_open_path(tmp)
		if not ok:
			ui.message(_("No se puede enviar la imagen a RayoAI. ¿Está funcionando?"))
			return

		if name:
			ui.message(_("Imagen URL enviada a RayoAI: %s") % name)
		else:
			ui.message(_("Imagen URL enviada a RayoAI"))

