import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
GUILD = 874248902130413588
API_KEY = os.getenv("API_KEY")
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")
SERVER_DB_USER = os.getenv("SERVER_DB_USER")
SERVER_DB_PASSWORD = os.getenv("SERVER_DB_PASSWORD")
SERVER_DB_NAME = os.getenv("SERVER_DB_NAME")
# API_URL = "http://localhost:8080/"
API_URL = f"http://{SERVER_IP}:8080/"

USERS_PROFILE_IMAGE_PATH = r"data/user_profile_image"
os.makedirs(USERS_PROFILE_IMAGE_PATH, exist_ok=True)

