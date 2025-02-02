import os

from PIL import Image
import torch
from torchvision import transforms
from transformers import AutoModelForImageSegmentation


def remove_background(image_path, model,output_path, device_type="cuda"):
    # تنظیمات پیش‌پردازش تصویر
    image_size = (1024, 1024)
    transform_image = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # بارگذاری تصویر
    image = Image.open(image_path)

    # پیش‌پردازش تصویر و انتقال به دستگاه مورد نظر
    input_images = transform_image(image).unsqueeze(0).to(device_type)

    # پیش‌بینی با مدل
    with torch.no_grad():
        preds = model(input_images)[-1].sigmoid().to(device_type)

    # پس‌پردازش مات آلفا
    pred = preds[0].squeeze()
    pred_pil = transforms.ToPILImage()(pred)
    mask = pred_pil.resize(image.size)

    # اضافه کردن مات آلفا به تصویر اصلی
    image.putalpha(mask)

    # ذخیره تصویر نهایی
    image.save(output_path)
    print(f"تصویر بدون پس‌زمینه در '{output_path}' ذخیره شد.")
    image_output_path = os.path.abspath(output_path)
    return image_output_path
