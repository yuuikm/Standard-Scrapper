import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup
import os
import pandas as pd
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import time

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


def get_dynamic_html(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service("msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=options)

    driver.get(url)
    time.sleep(5)
    html = driver.page_source
    driver.quit()
    return html


def download_image(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
    else:
        print(f"Не удалось скачать изображение: {url}")


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_width = draw.textbbox((0, 0), test_line, font=font)[2]

        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return "\n".join(lines)


def create_social_media_image(title, image_path, image_author, output_path):
    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    news_image = Image.open(image_path).convert("RGB")

    enhancer = ImageEnhance.Color(news_image)
    news_image = enhancer.enhance(2.5)

    target_height = 1000
    aspect_ratio = news_image.width / news_image.height
    new_width = int(target_height * aspect_ratio)
    news_image = news_image.resize((new_width, target_height))

    final_image = Image.new("RGB", template.size, (0, 0, 0))
    x_offset = (template.width - new_width) // 2
    final_image.paste(news_image, (x_offset, 0))
    final_image.paste(template, (0, 0), mask=template)

    draw = ImageDraw.Draw(final_image)
    max_text_width = 983 - 17
    text_x = 17
    text_y = 703
    text_bottom = 950
    max_text_height = text_bottom - text_y

    font_size = 80
    line_spacing = 15
    font = ImageFont.truetype(FONT_PATH, font_size)

    wrapped_text = wrap_text(draw, title.upper(), font, max_text_width)

    while True:
        lines = wrapped_text.split("\n")
        total_text_height = len(lines) * font_size + (len(lines) - 1) * line_spacing

        if total_text_height <= max_text_height or font_size <= 30:
            break

        font_size -= 2
        font = ImageFont.truetype(FONT_PATH, font_size)
        wrapped_text = wrap_text(draw, title.upper(), font, max_text_width)

    text_start_y = text_y + (max_text_height - total_text_height) // 2
    current_y = text_start_y

    for line in wrapped_text.split("\n"):
        text_width = draw.textbbox((0, 0), line, font=font)[2]
        centered_x = text_x + (max_text_width - text_width) // 2
        draw.text((centered_x, current_y), line, font=font, fill="white")
        current_y += font_size + line_spacing

    author_font = ImageFont.truetype(FONT_PATH, 15)
    author_x = 17
    author_y = 975
    draw.text((author_x, author_y), image_author.upper(), font=author_font, fill=(255, 255, 255, 80))

    final_image.save(output_path)
    print(f"✅ Создано изображение: {output_path}")


def scrape_pages():
    data = []

    for base_url in BASE_URLS:
        print(f"🔄 Загружаем страницу: {base_url}")
        html = get_dynamic_html(base_url)
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.select("table.table-striped tbody tr")[1:]

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            post_datetime = cols[0].text.strip()
            post_date, post_time = post_datetime.split(" ")
            if post_date != today_date:
                continue

            title_tag = cols[1].find("a")
            if not title_tag:
                continue

            title = title_tag.text.strip()
            post_url = title_tag["href"].strip()
            post_response = requests.get(post_url)
            post_soup = BeautifulSoup(post_response.text, "html.parser")
            image_tag = post_soup.select_one("div.entry__img-holder img")
            author_tag = post_soup.select_one("div.entry__img-holder span")
            image_author = author_tag.text.strip() if author_tag else ""

            data.append((post_datetime, title, post_url, image_author))

    data.sort(reverse=True, key=lambda x: x[0])

    for count, (_, title, post_url, image_author) in enumerate(data, 1):
        post_response = requests.get(post_url)
        post_soup = BeautifulSoup(post_response.text, "html.parser")

        image_tag = post_soup.select_one("div.entry__img-holder img")
        if not image_tag:
            continue

        image_url = "https://standard.kz" + image_tag["src"].strip()
        image_filename = os.path.join(IMAGE_DIR, f"{count}.jpg")

        download_image(image_url, image_filename)

        output_image_path = os.path.join(OUTPUT_DIR, f"post_{count}.png")
        create_social_media_image(title, image_filename, image_author, output_image_path)


if __name__ == "__main__":
    scrape_pages()