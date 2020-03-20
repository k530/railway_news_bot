#!/usr/bin/env python3
#coding:utf-8

import telegram
from log_err import *
import configparser
import crawl_12306_notice
import crawl_weibo


def generate_message(message):
    if message.get('title', '') != '':
        text = '<b>' + message['title'] + '</b>\n'
    else:
        text = ''
    text += message.get('content', '')
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[0:MAX_MESSAGE_LENGTH] + '......'
    if message.get('url', '') != '':
        text += ' (From: ' + message['url'] + ')'
    return text


def send_message(bot, chat_id, message_list):
    for message in message_list:
        try:
            text = generate_message(message)
            print(text)
            bot.sendMessage(chat_id=chat_id, text=text, parse_mode='html')
        except Exception as e:
            log_err({'err_module': 'send_message', 'err_info': str(e), 'err_content': str(message)})


def run_task(bot, chat_id, task_list):
    message_list = []
    for task in task_list:
        print(task)
        try:
            result = eval(task)
            if result.get('status') == 0:
                message_list += result['data']
            # print(result['data'])
        except Exception as e:
            log_err({'err_module': task, 'err_info': str(e), 'err_content': ''})
    send_message(bot, chat_id, message_list)


if __name__=='__main__':
    conf = configparser.ConfigParser()
    conf.read('bot.conf')
    CHAT_ID = conf.get("bot", "CHAT_ID")
    TOKEN = conf.get("bot", "TOKEN")
    task_file_name = conf.get("bot", "task_file_name")
    MAX_MESSAGE_LENGTH = int(conf.get("bot", "MAX_MESSAGE_LENGTH"))
    bot = telegram.Bot(token=TOKEN)
    # proxy = telegram.utils.request.Request(proxy_url='http://127.0.0.1:1080')
    # bot = telegram.Bot(token=TOKEN, request=proxy)
    # bot = ''
    task_list = []
    f = open(task_file_name, 'r', encoding='utf-8')
    for line in f.readlines():
        task = line.replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        if len(task) == 0:
            continue
        task_list.append(task)
    run_task(bot, CHAT_ID, task_list)
