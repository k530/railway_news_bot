#!/usr/bin/env python3
#coding:utf-8

import telegram
import configparser
import json
from datetime import datetime
from log_err import *
import crawl_12306_notice
import crawl_weibo


def generate_message(message, max_message_length=-1):
    if message.get('title', '') != '':
        text = '<b>' + message['title'] + '</b>\n'
    else:
        text = ''
    text += message.get('content', '')
    if max_message_length == -1:
        message_num = (len(text)//500)+int((len(text)%500) is not 0)
        text_list = []
        for i in range(0, message_num):
            if text[i: (i+1)*500] != '':
                text_list.append(text[i: (i+1)*500])
        text_list[-1] += '\n(Via: ' + message['url'] + ')'
        return text_list
    if len(text) > max_message_length:
        text = text[0:max_message_length] + '......'
    if message.get('url', '') != '':
        text += '\n(Via: ' + message['url'] + ')'
    return [text, ]


def send_message(bot, chat_id, message_list, max_message_length=-1):
    for message in message_list:
        try:
            text_list = generate_message(message, max_message_length)
            for text in text_list:
                print(chat_id)
                print(text)
                bot.sendMessage(chat_id=chat_id, text=text, parse_mode='html')
        except Exception as e:
            log_err({'err_module': 'send_message', 'err_info': str(e), 'err_content': str(message)})


def run_task(bot, task_list):
    for task in task_list:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), task)
        try:
            result = eval(task.get('eval', 'pass'))
            # print(result)
            if result.get('status') != 0:
                continue
            chat_list = task.get('chat', [])
            for chat in chat_list:
                if 'id' in chat:
                    send_message(bot, chat['id'], result['data'], chat.get('max_message_length', -1))
            # print(result['data'])
        except Exception as e:
            log_err({'err_module': task, 'err_info': str(e), 'err_content': ''})


if __name__=='__main__':
    conf = configparser.ConfigParser()
    conf.read('bot.conf')
    TOKEN = conf.get("bot", "TOKEN")
    task_file_name = conf.get("bot", "task_file_name")
    bot = telegram.Bot(token=TOKEN)
    # proxy = telegram.utils.request.Request(proxy_url='http://127.0.0.1:1080')
    # bot = telegram.Bot(token=TOKEN, request=proxy)
    # bot = ''
    task_file = open(task_file_name, 'r', encoding='utf-8')
    run_task(bot, json.load(task_file).get('tasks', []))
