import os


def load_history_file(file_name):
    if not os.path.exists(file_name):
        f = open(file_name, 'w', encoding='utf-8')
        f.close()
        return []
    f = open(file_name, 'r', encoding='utf-8')
    old_list = []
    for line in f.readlines():
        if line.replace('\n', '').replace('\r', '') != '':
            old_list.append(line.replace('\n', '').replace('\r', ''))
    f.close()
    return old_list


def write_history_file(file_name, new_list, hash_key):
    f = open(file_name, 'w', encoding='utf-8')
    for new_item in new_list:
        if new_item.get(hash_key, '') == '':
            continue
        f.write(new_item[hash_key])
        f.write('\n')
    f.close()
