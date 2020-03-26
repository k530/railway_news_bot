from datetime import datetime


def log_err(err_dict):
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + 'Error: ')
    print(err_dict)
    f = open('err_log.txt', 'a')
    f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+',')
    f.write(str(err_dict.get('err_module', ''))+',')
    f.write(str(err_dict.get('err_info', ''))+',')
    f.write(str(err_dict.get('err_content', '')).replace('\n', '').replace('\r', ''))
    f.write('\n')
    f.close()
