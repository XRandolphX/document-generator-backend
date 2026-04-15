"""
config.py
---------
Carga y expone las variables de entorno necesarias para el funcionamiento
de la aplicación.

Variables requeridas en el archivo ``.env``:
    API_KEY (str): Clave de autenticación para la API de OpenRouter.
"""

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
