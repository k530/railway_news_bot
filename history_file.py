import os
from datetime import datetime, timedelta


def load_history_file(file_name):
    if not os.path.exists(file_name):
        f = open(file_name, 'w', encoding='utf-8')
        f.close()
        return []
    f = open(file_name, 'r', encoding='utf-8')
    old_list = {}
    for line in f.readlines():
        if line.replace('\n', '').replace('\r', '') != '':
            time_str, name_str = line.replace('\n', '').replace('\r', '').split(',')
            old_list[name_str] = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    f.close()
    return old_list


def write_history_file(file_name, new_list):
    f = open(file_name, 'w', encoding='utf-8')
    for new_key in new_list:
        if datetime.now() - new_list[new_key] > timedelta(days=14):
            continue
        f.write(new_list[new_key].strftime('%Y-%m-%d %H:%M:%S'))
        f.write(',')
        f.write(new_key)
        f.write('\n')
    f.close()
