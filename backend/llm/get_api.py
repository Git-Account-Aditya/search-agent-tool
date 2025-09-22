from dotenv import load_dotenv
import os

load_dotenv()
def load_apikey():
    return os.getenv('GROQ_API_KEY', '')