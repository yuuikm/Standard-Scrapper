import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = "7696195944:AAEW7CPw5GJ3_zFh-UprrmWri3mHWE7ynsA"
TELEGRAM_CHANNEL_ID = "@standardkz"

BASE_URLS = [
    "https://standard.kz/ru/post/archive",
    "https://standard.kz/kz/post/archive"
]

TEMPLATE_PATH = "psd/post-image.png"
IMAGE_DIR = "scraped_images"
OUTPUT_DIR = "generated_posts"
FONT_PATH = "font/Montserrat-Bold.ttf"

today_date = datetime.now().strftime("%d.%m.%Y")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
