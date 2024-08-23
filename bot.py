#!/usr/bin/env python3

import telebot
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from loguru import logger

from dotenv import load_dotenv

load_dotenv()

logger.add("bot_log.log", rotation="10 MB", compression="zip", level="DEBUG")

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.username}")
    bot.reply_to(message, "Привет! Отправь мне ссылку на видео, и я скачаю mp3 или mp4 для тебя.")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    logger.info(f"Получена ссылка: {url} от пользователя {message.from_user.username}")

#TODO Поправить логирование
    if 'youtube.com' in url or 'youtu.be' in url:

        markup = telebot.types.InlineKeyboardMarkup()
        #TODO Пофиксить проблему с превышением 64 байт в callback_data
        btn_mp3 = telebot.types.InlineKeyboardButton(text="Скачать MP3", callback_data=f"mp3|{url}")
        btn_mp4 = telebot.types.InlineKeyboardButton(text="Скачать MP4", callback_data=f"mp4|{url}")
        markup.add(btn_mp3, btn_mp4)
        bot.send_message(message.chat.id, "Выберите формат для скачивания:", reply_markup=markup)

    else:
        logger.warning(f"Неверная ссылка от пользователя {message.from_user.username}: {url}")
        bot.reply_to(message, "Пожалуйста, отправьте действующую ссылку на видео с YouTube.")



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    format_type, url = call.data.split('|')
    logger.info(f"Пользователь {call.from_user.username} выбрал формат {format_type} для ссылки {url}")

    try:
        yt = YouTube(url, on_progress_callback = on_progress)

        if format_type == 'mp3':

            ys = yt.streams.get_audio_only()
            audio_file = ys.download(mp3=True)
        
            # Отправляем аудио обратно пользователю
            with open(audio_file, 'rb') as audio:
                bot.send_audio(call.message.chat.id, audio)
                logger.info(f"Успешно отправлен MP3 файл пользователю {call.from_user.username}")
        
            # Удаляем файл после отправки
            os.remove(audio_file)


        elif format_type == 'mp4':

            ys = yt.streams.get_highest_resolution()
            video_file = ys.download(timeout=15, max_retries=3)
            
            # Отправляем видео обратно пользователю
            with open(video_file, 'rb') as video:
                bot.send_video(call.message.chat.id, video)
                logger.info(f"Успешно отправлен MP4 файл пользователю {call.from_user.username}")
        
            # Удаляем файл после отправки
            os.remove(video_file)

            
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса от пользователя {call.from_user.username}: {str(e)}")
        bot.reply_to(call.message, f"Произошла ошибка: введенная Вами ссылка скорее всего некорректна, повторите попытку.")
    
    del yt

# Запускаем бота
logger.info("Бот запущен и готов к работе")
bot.polling()