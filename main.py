import os
import json
import logging
import asyncio
import random
from aiohttp import ClientSession
from bs4 import BeautifulSoup

API_TOKEN = os.getenv("API_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SENT_LIST_FILE = 'dump.json'
KEYWORDS = [
    "открытие фонтанов 2025",
    "открытие фонтанов 2026",
    "открытие светомузыкального фонтана 2025",
]
IGNORE_WORDS = {"Петергоф", "нефть", "недр", "месторождение"}
IGNORE_SITES = {"instagram", "livejournal", "fontanka", "avito"}
logging.basicConfig(level=logging.INFO)
def load_sent_list():
    """Загружает список ранее отправленных сообщений."""
    try:
        with open(SENT_LIST_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
def save_sent_list(sent_list):
    """Сохраняет список отправленных сообщений."""
    with open(SENT_LIST_FILE, 'w', encoding='utf-8') as file:
        json.dump(sent_list, file)
def clean_url_google(url):
    """Очищает URL от лишних параметров (для Google)."""
    url = url[len('/url?q='):]
    return url.split('&sa=U&ved')[0]
def clean_url_yandex(url):
    """Очищает URL от лишних параметров (для Яндекса)."""
    url = url[len('https://'):]
    return url.split('&&&&&')[0]
async def send_message(session, message_text):
    """Отправляет сообщение в Telegram-канал."""
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHANNEL_ID,
        'text': message_text,
        'parse_mode': 'Markdown'
    }
    async with session.post(url, json=payload) as response:
        if response.status == 200:
            logging.info('Сообщение успешно отправлено.')
        else:
            logging.error(f'Ошибка отправки сообщения: {response.status}')
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15'
]
async def search_google(session, keyword):
    """Выполняет поиск по Google."""
    query = f'https://www.google.ru/search?q={keyword}&hl=ru&tbs=qdr:d'
    headers = {'User-Agent': random.choice(user_agents)}
    async with session.get(query, headers=headers) as response:
        if response.status != 200:
            logging.error(f'Ошибка при обращении к Google: {response.status}')
            return []
        soup = BeautifulSoup(await response.text(), 'html.parser')
        results = []
        for item in soup.find_all('h3'):
            parent_link = item.find_parent('a')
            if parent_link and 'href' in parent_link.attrs:
                link = clean_url_google(parent_link['href'])
                results.append((item.get_text(), link))
        return results
async def search_yandex(session, keyword):
    """Выполняет поиск по Яндексу."""
    query = f'https://yandex.ru/search/?text={keyword}&within=77'
    headers = {'User-Agent': random.choice(user_agents)}
    async with session.get(query, headers=headers) as response:
        if response.status != 200:
            logging.error(f'Ошибка при обращении к Yandex: {response.status}')
            return []
        soup = BeautifulSoup(await response.text(), 'html.parser')
        results = []
        for item in soup.find_all('h3'):
            parent_link = item.find_parent('a')
            if parent_link and 'href' in parent_link.attrs:
                link = clean_url_yandex(parent_link['href'])
                results.append((item.get_text(), link))
        return results
async def main():
    """Главная функция программы."""
    sent_set = set(load_sent_list())
    async with ClientSession() as session:
        tasks = []
        for keyword in KEYWORDS:
            tasks.append(asyncio.create_task(search_google(session, keyword)))
            tasks.append(asyncio.create_task(search_yandex(session, keyword)))
        responses = await asyncio.gather(*tasks)
        for response in responses:
            for title, link in response:
                if not any(word in title for word in IGNORE_WORDS) and link not in IGNORE_SITES:
                    if (title, link) not in sent_set:
                        if "google" in link:
                            message_text = f"{title}\n{link}\n⛲@MonitoringFontan📰#google"
                        elif "yandex" in link:
                            message_text = f"{title}\n{link}\n⛲@MonitoringFontan📰#yandex"
                        else:
                            continue
                        await send_message(session, message_text)
                        sent_set.add((title, link))
                        await asyncio.sleep(random.randint(5, 15))
    save_sent_list(list(sent_set))
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
