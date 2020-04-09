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


def write_history_file(file_name, new_list, max_size=-1, delta_days=5):
    f = open(file_name, 'w', encoding='utf-8')
    skip = 0
    new_list = sorted(new_list.items(), key=lambda x: x[1])
    for record in new_list:
        if (max_size != -1) and (len(new_list) - skip > max_size) and \
                (datetime.now() - record[1] > timedelta(days=delta_days)) and \
                (r'https://www.12306.cn/mormhweb/zxdt/20' not in record[0]):
            skip += 1
            continue
        f.write(record[1].strftime('%Y-%m-%d %H:%M:%S'))
        f.write(',')
        f.write(record[0])
        f.write('\n')
    f.close()
