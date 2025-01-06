FROM python:3.11.6-slim

WORKDIR /app

COPY . /app

RUN pip install aiogram

RUN pip install rss-parser

RUN pip install requests

CMD ["python", "main.py"]
