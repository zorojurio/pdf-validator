import os

from dotenv import load_dotenv

load_dotenv()
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
