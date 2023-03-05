import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("VOCODE_API_KEY")
BASE_URL = "napi.vocode.dev"