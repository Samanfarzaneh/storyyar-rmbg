import os
import uuid
import torch
from io import BytesIO
from PIL import Image
from fastapi import FastAPI, status, HTTPException
import requests
from pydantic import BaseModel
from transformers import AutoModelForImageSegmentation

from auth import verify_api_key
from remove_background.RMBG_main import remove_background

app = FastAPI()

device_type = "cuda"
device = torch.device(device_type)
print(f"Using device: {device}")

# بارگذاری مدل
model = AutoModelForImageSegmentation.from_pretrained('briaai/RMBG-2.0', trust_remote_code=True)

# تنظیم دقت محاسباتی (اختیاری)
torch.set_float32_matmul_precision('high')

# انتقال مدل به دستگاه مورد نظر
model.to(device)
model.eval()

# ایجاد پوشه temp در صورت عدم وجود
if not os.path.exists('temp'):
    os.makedirs('temp')

# مدل Pydantic برای دریافت پارامترهای درخواست
class ImageRequest(BaseModel):
    image_url: str  # پارامتر image_url از نوع رشته
    api_key: str  # اضافه کردن api_key برای احراز هویت


@app.post("/")
async def remove_background_api(request: ImageRequest):

    verify_api_key(api_key=request.api_key)

    image_url = request.image_url  # دسترسی به URL تصویر

    # دانلود تصویر از URL
    response = requests.get(image_url)

    if response.status_code == 200:
        # تبدیل تصویر به آبجکت PIL
        image = Image.open(BytesIO(response.content))

        # تولید نام یکتا با استفاده از uuid
        unique_filename = str(uuid.uuid4()) + ".png"
        image_path = os.path.join('temp', unique_filename)  # ذخیره تصویر در پوشه temp
        image.save(image_path)

        # حذف پس‌زمینه
        output_filename = str(uuid.uuid4()) + ".png"
        output_path = os.path.join('temp', output_filename)  # ذخیره تصویر خروجی با نام یکتا
        remove_background(image_path, model, output_path)

        # **آپلود تصویر به API موردنظر**
        headers = {
            "Authorization": "jYsrJRAsiIez8LeMWsyDyPGUIQY4HE9ZtR9Zk708TsXWXK5RkkWB5KRqMFdwLwFD"
        }

        # **آپلود تصویر به API موردنظر**
        with open(output_path, "rb") as img_file:
            files = {"image": (output_path, img_file, "image/png")}  # کلید `file` برای ارسال تصویر
            upload_response = requests.post(
                "https://app.coverlydesign.com/api/v1/storage",
                headers=headers,  # هدر Authorization اضافه شده است
                files=files
            )

        print("Upload response status code:", upload_response.status_code)
        print("Upload response text:", upload_response.text)

        # اگر آپلود موفقیت‌آمیز بود، عکس‌ها را پاک کن
        if upload_response.status_code == 200:
            # پاک‌سازی فایل‌ها
            os.remove(image_path)
            os.remove(output_path)
            return {"message": "Image processed and uploaded successfully"}
        else:
            # پاک‌سازی فایل‌های پردازش شده حتی اگر آپلود موفقیت‌آمیز نباشد
            os.remove(image_path)
            os.remove(output_path)
            return {"error": "Image processing done, but upload failed"}

    else:
        raise HTTPException(status_code=400, detail="Unable to fetch image from the provided URL")
