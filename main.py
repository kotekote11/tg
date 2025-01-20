import os
import json
import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from aiogram import Bot
import random

# Load environment variables
API_TOKEN = os.getenv("API_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SENT_LIST_FILE = 'dump.json'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Keywords for search
KEYWORDS = [
    "открытие фонтанов 2025",
    "открытие фонтанов 2026",
    "открытие светомузыкального фонтана 2025"
]

# Ignore sets for filtering
IGNORE_WORDS = {"Петергоф", "нефть", "недр", "месторождение"}
IGNORE_SITES = {"instagram", "livejournal", "fontanka", "avito"}

# User agents for randomness
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
]

# Load sent URLs and initialize sent set
def load_sent_list():
    try:
        with open(SENT_LIST_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Save sent URLs
def save_sent_list(sent_list):
    with open(SENT_LIST_FILE, 'w', encoding='utf-8') as file:
        json.dump(sent_list, file)

# Clean URLs from Google
def clean_url_google(url):
    url = url[len('/url?q='):]
    return url.split('&sa=U&ved')[0]

# Clean URLs from Yandex
def clean_url_yandex(url):
    url = url[url.index('http'):].split('&&&&&')[0]
    return url

# Function to search Google for articles
async def search_google(session, keyword):
    query = f'https://www.google.ru/search?q={keyword}&hl=ru&tbs=qdr:d'
    headers = {'User-Agent': random.choice(user_agents)}
    async with session.get(query, headers=headers) as response:
        if response.status != 200:
            logging.error(f'Ошибка при обращении к Google: {response.status}')
            return []
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        for item in soup.find_all('h3'):
            link = item.find('a')['href']
            cleaned_link = clean_url_google(link)
            articles.append(cleaned_link)
        return articles

# Function to search Yandex for articles
async def search_yandex(session, keyword):
    query = f'https://yandex.ru/search/?text={keyword}&within=77'
    headers = {'User-Agent': random.choice(user_agents)}
    async with session.get(query, headers=headers) as response:
        if response.status != 200:
            logging.error(f'Ошибка при обращении к Yandex: {response.status}')
            return []
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        articles = []
        for item in soup.find_all('a', href=True):
            cleaned_link = clean_url_yandex(item['href'])
            articles.append(cleaned_link)
        return articles

# Main monitoring function
async def monitor():
    sent_set = set(load_sent_list())
    bot = Bot(token=API_TOKEN)

    async with aiohttp.ClientSession() as session:
        for keyword in KEYWORDS:
            logging.info("Checking keyword: %s", keyword)

            # Random sleep before searching to avoid rate limiting
            await asyncio.sleep(random.randint(10, 30))

            # Search Google and Yandex
            news_from_google = await search_google(session, keyword)
            news_from_yandex = await search_yandex(session, keyword)

            # Process Google news
            for link in news_from_google:
                if link not in sent_set and not any(word in link for word in IGNORE_WORDS):
                    title = link  # This placeholder should ideally fetch the title
                    message_text_google = f"{title}\n{link}\n⛲@MonitoringFontan📰#google"
                    await bot.send_message(chat_id=CHANNEL_ID, text=message_text_google)
                    sent_set.add(link)
                    logging.info("Sent Google message: %s", message_text_google)
                    await asyncio.sleep(random.randint(5, 15))

            # Process Yandex news
            for link in news_from_yandex:
                if link not in sent_set and not any(word in link for word in IGNORE_WORDS):
                    title = link  # This placeholder should ideally fetch the title
                    message_text_yandex = f"{title}\n{link}\n⛲@MonitoringFontan📰#yandex"
                    await bot.send_message(chat_id=CHANNEL_ID, text=message_text_yandex)
                    sent_set.add(link)
                    logging.info("Sent Yandex message: %s", message_text_yandex)
                    await asyncio.sleep(random.randint(5, 15))

        save_sent_list(list(sent_set))

if __name__ == "__main__":
    # Start monitoring
    loop = asyncio.get_event_loop()
    loop.run_until_complete(monitor())
