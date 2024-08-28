import telebot
import requests
from bs4 import BeautifulSoup
import time
import os

CHANNEL_ID = '@tmanybottest'
NEWS_URL = 'https://t.me/s/rybar?q=%23дайджест'
bot = telebot.TeleBot(os.environ['tt'])
sent_news = set()

def send_news():
    response = requests.get(NEWS_URL)
    soup = BeautifulSoup(response.text.replace("<br/>", "\n"), 'html.parser')
    news = soup.find_all('div', class_='tgme_widget_message_text js-message_text')
    for item in news:
        news_text = item.text.strip()
        if news_text not in sent_news:
            bot.send_message(CHANNEL_ID, news_text)
            sent_news.add(news_text)
        time.sleep(1)

while True:
    try:
        send_news()
        time.sleep(5 * 60)
    except Exception as e:
        print('Ошибка:', e)
