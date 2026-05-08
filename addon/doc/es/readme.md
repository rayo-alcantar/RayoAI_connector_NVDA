# RayoAI Connector para NVDA

Un complemento para NVDA que te permite enviar imágenes rápidamente a la aplicación de escritorio RayoAI para describirlas o analizarlas.

- Captura la imagen del elemento actual del navegador de objetos de NVDA y la envía a RayoAI.
- La comunicación es local (127.0.0.1) por un puerto configurable. No se envían píxeles; solo se comparte la ruta a un archivo temporal en tu equipo.

## Requisitos

- Windows 10 u 11 (x64).
- NVDA 2023.1 o superior.
- Aplicación de escritorio RayoAI instalada y en ejecución.

## Instalación

1. Descarga el archivo del complemento (.nvda-addon) desde la página de lanzamientos del proyecto:
   https://github.com/rayo-alcantar/RayoAI_connector_NVDA/releases
   Desde la web oficial, o en el propio RayoAI.
2. Abre el Administrador de complementos de NVDA:
   Menú NVDA → Herramientas → Administrador de complementos → Instalar…
3. Selecciona el archivo .nvda-addon que descargaste y acepta.
4. Reinicia NVDA cuando se te solicite.

Durante la instalación, puede aparecer un mensaje invitando a realizar una donación. Es totalmente opcional.

## Configuración (puerto local)

- Menú NVDA → Preferencias → Ajustes → RayoAI Connector.
- Ajusta el “puerto para conectarse a RayoAI” si tu aplicación RayoAI no usa el valor predeterminado (opción a futuro).
- Puerto por defecto: 16180.

La comunicación se realiza únicamente con 127.0.0.1 (tu propio equipo).

## Uso rápido

El complemento trabaja con el “navegador de objetos” de NVDA (el elemento que NVDA usa para revisar lo que hay en la pantalla). Sitúa el navegador de objetos sobre el elemento que te interesa y usa este atajo:

- NVDA+Shift+K: Capturar lo que se ve del elemento y enviarlo a RayoAI.
  - Útil cuando el elemento es visible en pantalla (por ejemplo, una imagen, botón, control, etc.).
  - El complemento toma una captura del área en pantalla de ese elemento y guarda un BMP temporal.

Consejo: si lo prefieres, puedes personalizar este atajo en Menú NVDA → Preferencias → Gestos de entrada → categoría “RayoAI Connector”.

## Pasos detallados de uso

1) Enviar una captura del elemento (NVDA+Shift+K)
- Navega con NVDA hasta el elemento que te interesa (usa el navegador de objetos).
- Asegúrate de que el elemento sea visible en pantalla (no oculto ni fuera del área visible).
- Pulsa NVDA+Shift+K.
- Si todo va bien, RayoAI recibirá el archivo y lo abrirá para que puedas trabajar con él.

## Notas y limitaciones

- Cortina de pantalla: si usas la “cortina de pantalla” de NVDA, desactívala antes de tomar capturas. El complemento te avisará si está activa.
- Elementos sin ubicación: algunos elementos no informan su posición en pantalla; en ese caso no se puede capturar su imagen.
- Archivos temporales: las imágenes se guardan en tu carpeta temporal del sistema y pueden eliminarse automáticamente más adelante.

## Privacidad y seguridad

- La conexión es solo con 127.0.0.1 (tu equipo) y por el puerto configurado.
- Se envía a RayoAI únicamente la ruta de un archivo temporal; no se transmiten datos de pantalla por la red.

## Solución de problemas

- “No se puede enviar la imagen a RayoAI. ¿Está abierto y funcionando?”
  - Abre la aplicación RayoAI y verifica que está en ejecución.
  - Revisa el puerto en Ajustes → RayoAI Connector y que coincida con el de RayoAI (no es necesario hacer nada por ahora).
- “No se puede capturar la imagen del navegador de objetos.”
  - Asegúrate de que el elemento sea visible y la cortina de pantalla esté desactivada.
  - Prueba a desplazarte o acercar/alejar para que el elemento quede completamente en pantalla.

## Personalizar atajos de teclado

- Menú NVDA → Preferencias → Gestos de entrada → “RayoAI Connector”.
- Puedes reasignar NVDA+Shift+K si entra en conflicto con otros gestos.

## Desinstalación

- Menú NVDA → Herramientas → Administrador de complementos.
- Selecciona “RayoAI connector for NVDA” y pulsa “Quitar…”.
- Reinicia NVDA.

## Dónde obtener ayuda o actualizaciones

- Código fuente y descargas: https://github.com/rayo-alcantar/RayoAI_connector_NVDA
Correo del desarrollador: angelalcantar@rayoscompany.com

## Licencia

- Este complemento está cubierto por la Licencia Pública General de GNU (consulta el archivo COPYING.txt incluido en el proyecto).

---

Información técnica (solo si te interesa):
- El complemento abre una conexión TCP local (127.0.0.1) al puerto configurado (por defecto 16180) y envía un mensaje JSON simple con la ruta de la imagen. La aplicación RayoAI es quien abre el archivo y lo procesa.
- Para NVDA+Shift+K se realiza una captura directa de la región del elemento en pantalla (GDI de Windows) y se guarda como BMP de 24 bits en una carpeta temporal.
