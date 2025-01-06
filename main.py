import requests
import json
import random
import time
import logging
from xml.etree import ElementTree as ET
import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SAVED_NEWS_FILE = 'sent_news.json'  # Файл для сохранения отправленных новостей
RSS_URL = 'https://habr.com/ru/rss/news/?fl=ru'

# Загрузка отправленных новостей из файла
def load_sent_news():
    try:
        with open(SAVED_NEWS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Сохранение отправленных новостей в файл
def save_sent_news(sent_news):
    with open(SAVED_NEWS_FILE, 'w') as f:
        json.dump(sent_news, f)

# Отправка сообщения в Telegram
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    response = requests.post(url, data=data)
    return response.json()

# Получение новостей из RSS
def get_news():
    response = requests.get(RSS_URL)
    return ET.fromstring(response.content)

# Главная логика
def main():
    sent_news = load_sent_news()
    all_news = get_news()

    items = all_news.findall('.//item')
    # Извлечение новостей, которых еще нет в sent_news
    news_to_send = [item for item in items if item.find('link').text not in sent_news]

    if news_to_send:
        # Выбор случайной новости
        selected_news = random.choice(news_to_send)
        title = selected_news.find('title').text
        link = selected_news.find('link').text
        message = f'<b>{title}</b>\n{link}'

        # Отправка сообщения в Telegram
        response = send_telegram_message(message)
        if response.get('ok'):
            logging.info(f'Отправлено: {title}')
            # Сохраняем отправленную новость
            sent_news.append(link)
            save_sent_news(sent_news)
        else:
            logging.error(f'Ошибка отправки: {response}')

    else:
        logging.info('Нет новых новостей для отправки')

if __name__ == "__main__":
    while True:
        main()
        time.sleep(200)  # Подождите 200 секунд перед следующим запросом
