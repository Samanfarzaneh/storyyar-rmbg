from dotenv import load_dotenv
import os

# بارگذاری فایل .env
load_dotenv()

# خواندن API Key از فایل .env
API_KEY = os.getenv("API_KEY")
