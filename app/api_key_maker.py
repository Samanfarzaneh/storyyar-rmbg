import os
import secrets

# ایجاد یک API Key تصادفی
api_key = secrets.token_hex(32)  # 32 بایت به صورت هگزادسیمال
print("Generated API Key:", api_key)
