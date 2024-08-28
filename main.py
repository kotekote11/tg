import telebot
import requests
from bs4 import BeautifulSoup
import time
import os
import configparser
import datetime
import feedparser

import pip
pip.main(['install', 'telebot'])

config = configparser.ConfigParser()
config.read('settings.ini')
DATETIME = config.get('rybar', 'DATETIME')

CHANNEL_ID = '@tmanybottest'
NEWS_URL = 'https://t.me/s/rybar?q=%23дайджест'
bot = telebot.TeleBot(os.environ['tt'])
sent_news = set()

def send_news():
    response = requests.get(NEWS_URL)
    soup = BeautifulSoup(response.text.replace("<br/>", "\n"), 'html.parser')
    news = soup.find_all('div', class_='tgme_widget_message_text js-message_text')
    dates = soup.find_all('time')

    for n, item in enumerate(news):
        news_text = item.text.strip()
        news_date = dates[n].text.strip()
        if news_text not in sent_news:
            bot.send_message(CHANNEL_ID, news_text)
            sent_news.add(news_text)
            time.sleep(1)

            # Update the DATETIME value in the settings.ini file
            post_time = datetime.datetime.now()  # Get the current timestamp
            new_datetime = post_time.strftime('%Y-%m-%d %H:%M:%S%z')
            print('New datetime:', new_datetime)
            config.set('rybar', 'DATETIME', new_datetime)
            with open('settings.ini', 'w') as config_file:
                config.write(config_file)

            print('Message creation date:', news_date)

    rss = feedparser.parse(NEWS_URL)
    for post in reversed(rss.entries):
        data = post.published
        post_time = datetime.datetime.strptime(data, '%a, %d %b %Y %H:%M:%S %z')
        time_old = datetime.datetime.strptime(DATETIME, '%Y-%m-%d  %H:%M:%S%z')

        # Skip already published posts
        if post_time <= time_old:
            continue
        else:
            # Send the new post message
            news_text = post.title
            bot.send_message(CHANNEL_ID, news_text)
            time.sleep(1)

            # Update the DATETIME value in the settings.ini file
            new_datetime = post_time.strftime('%Y-%m-%d %H:%M:%S%z')
            print('New datetime:', new_datetime)
            config.set('rybar', 'DATETIME', new_datetime)
            with open('settings.ini', 'w') as config_file:
                config.write(config_file)

            print('Message creation date:', post_time.strftime('%Y-%m-%d %H:%M:%S%z'))

    print('Updated DATETIME:', config.get('rybar', 'DATETIME'))


while True:
    try:
        send_news()
        time.sleep(1 * 60)
    except Exception as e:
        print('Ошибка—:', e)
