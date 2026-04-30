"""
config.py
---------
Loads and exposes the environment variables required for the application
to function.

Required variables in the ``.env`` file:
    API_KEY (str): Authentication key for the OpenRouter API.
"""

import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
