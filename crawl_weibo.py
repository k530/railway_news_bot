import requests
import json
import re
from urllib import parse
import time
from datetime import datetime, timedelta
from history_file import *
from log_err import *
from format_weibo_datetime import *

requests.packages.urllib3.disable_warnings()


def format_weibo_content(content):
    try:
        content = content.replace('\n', '@line@').replace('\r', '@line@')
        content = content.replace('</div>', '@line@').replace('</p>', '@line@').replace('<br/>', '@line@')
        content = re.sub(r'<.*?>.*?</.*?>', '', content)
        content = re.sub(r'<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});', '', content)
        content = re.sub(r'[\r\n]+', '\n', content.replace('@line@', '\n'))
    except Exception as e:
        log_err({'err_module': 'format_weibo_content', 'err_info': str(e), 'err_content': content})
    finally:
        return content


def query_weibo_content(weibo_id):
    retry = 3
    text = ''
    while retry > 0:
        try:
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'dnt': '1',
                'mweibo-pwa': '1',
                'referer': 'https://m.weibo.cn/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/80.0.3987.132 Safari/537.36'
            }
            req = requests.get('https://m.weibo.cn/statuses/extend?id=' + str(weibo_id), headers=headers, verify=False)
            text = req.text
            time.sleep(2)
            weibo_content = json.loads(req.content).get('data', {}).get('longTextContent')
            # weibo_content = re.sub(r'<.*?>.*?<.*?>', '', weibo_content)
            weibo_content = re.sub(r'<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});', '', weibo_content)
            # print(weibo_content)
            title = re.match(r'(^【.*?】)|(^#.*?#)', weibo_content)
            if title is not None:
                title = title.group(0)
                weibo_content = weibo_content[len(title):]
                title = title[1:-1]
            else:
                title = ''
            # print({'status': 0, 'title': title, 'content': weibo_content})
            return {'status': 0, 'title': title, 'content': format_weibo_content(weibo_content)}
        except Exception as e:
            retry = retry - 1
            if retry == 0:
                log_err({'err_module': 'query_notice_content', 'err_info': str(e),
                         'err_content': 'URL:' + 'https://m.weibo.cn/statuses/extend?id=' + str(weibo_id) +
                                        ' content:' + text})
                return {'status': -1, 'err_info': str(e), 'err_content': 'URL:' +
                                                                         'https://m.weibo.cn/statuses/extend?id=' + str(
                    weibo_id) + ' content:' + text}


def query_weibo_list(suffix, delta_days):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'dnt': '1',
        'mweibo-pwa': '1',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.132 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    weibo_list = {}
    next_since_id = ''
    url = 'https://m.weibo.cn/api/container/getIndex?' + suffix
    # print(url)
    retry = 3
    text = ''
    while retry > 0:
        try:
            req = requests.get(url, headers=headers, verify=False)
            text = req.text
            time.sleep(2)
            weibo_list = json.loads(req.content)
            # print(weibo_list)
            if (weibo_list.get('ok') != 1) or ('data' not in weibo_list) or \
                    ('cards' not in weibo_list['data']):
                raise Exception('Illegal Data!')
            next_since_id = weibo_list['data'].get('cardlistInfo', {}).get('since_id', '')
            # print(next_since_id)
            break
        except Exception as e:
            retry = retry - 1
            if retry == 0:
                log_err({'err_module': 'query_weibo_list', 'err_info': str(e),
                         'err_content': 'URL:' + url + ' content:' + text})
                return {'status': -1, 'err_info': str(e),
                        'err_content': 'URL:' + url + ' content:' + text}
    try:
        weibo_id_list = []
        for card in weibo_list['data']['cards']:
            if (card.get('card_type') != 9) or ('mblog' not in card) or ('scheme' not in card):
                continue
            try:
                is_top = int(card['mblog'].get('mblogtype', 0))
                if is_top == 2:
                    create_time = format_weibo_datetime(card['mblog'].get('created_at', '2000-01-01'))
                    if datetime.now() - create_time > timedelta(days=delta_days):
                        continue
                scheme = re.match(r'https://m.weibo.cn/status/.*?\?mblogid', card['scheme'])
                if scheme is not None:
                    scheme = scheme.group(0)[26:-8]
                weibo_id = card['mblog'].get('id', '')
                user_id = card['mblog'].get('user', {}).get('id')
                if weibo_id == '':
                    raise Exception('Empty Weibo ID!')
                edit_time = card['mblog'].get('edit_at', '')
                if (scheme is not None) and (user_id is not None):
                    url = 'https://weibo.com/' + str(user_id) + '/' + str(scheme)
                else:
                    url = 'https://m.weibo.cn/detail/' + str(weibo_id)
                if edit_time != '':
                    edit_time = datetime.strptime(edit_time, '%a %b %d %H:%M:%S +0800 %Y')
                    weibo_id_list.append({'hash': weibo_id + '@' + edit_time.strftime('%Y-%m-%d %H:%M:%S'),
                                          'id': weibo_id, 'url': url})
                else:
                    weibo_id_list.append({'hash': weibo_id, 'id': weibo_id, 'url': url})
                # print(weibo_id)
            except Exception as e:
                log_err({'err_module': 'query_weibo_list', 'err_info': str(e),
                         'err_content': card.get('mblog') + ' URL: ' + url})
                continue
        # print(weibo_id_list)
        return {'status': 0, 'data': weibo_id_list, 'since': next_since_id}
    except Exception as e:
        log_err({'err_module': 'query_weibo_list', 'err_info': str(e),
                 'err_content': 'URL:' + url + ' content:' + text})
        return {'status': -1, 'err_info': str(e),
                'err_content': 'URL:' + url + ' content:' + text}


def check_weibo_update(first, suffix, user_name, page_num, page_turn_type, delta_days, select_reg=None):
    if select_reg is None:
        select_reg = {}
    weibo_list = []
    current_result = query_weibo_list(suffix, delta_days)
    if current_result['status'] != 0:
        return {'status': -1}
    weibo_list += current_result['data']
    if page_turn_type == 0:
        since_id = current_result['since']
        count = 1
        while (count < page_num) and (since_id != ''):
            current_result = query_weibo_list(suffix + '&since_id=' + str(since_id), delta_days)
            if current_result['status'] != 0:
                return {'status': -1}
            weibo_list += current_result['data']
            since_id = current_result['since']
            count += 1
    if page_turn_type == 1:
        for page_no in range(1, page_num):
            current_result = query_weibo_list(suffix + '&page=' + str(page_no + 1), delta_days)
            if current_result['status'] != 0:
                return {'status': -1}
            weibo_list += current_result['data']
    # print(weibo_list)
    if first:
        new_weibo_list = {}
        for weibo in weibo_list:
            new_weibo_list[weibo['hash']] = datetime.now()
        write_history_file('weibo_' + str(user_name) + '.txt', new_weibo_list)
        return {'status': 0, 'data': []}

    old_weibo_list = load_history_file('weibo_' + str(user_name) + '.txt')
    diff = []
    for weibo in weibo_list:
        if weibo.get('hash', '') == '':
            continue
        if str(weibo['hash']) not in old_weibo_list:
            diff.append(weibo)
    if diff:
        print('Old List: ', old_weibo_list.keys())
        print('Diff: ', diff)
        diff.reverse()

    message_list = []
    for article in diff:
        article_data = query_weibo_content(article['id'])
        if article_data['status'] != 0:
            continue
        if '@' in article['hash']:
            for hash_key in list(old_weibo_list.keys()):
                if hash_key[0:len(article['id'])] == article['id']:
                    old_weibo_list.pop(hash_key)
        old_weibo_list[article['hash']] = datetime.now()
        if ('title' in select_reg) and (re.match(select_reg['title'], article_data.get('title', '')) is None):
            continue
        if ('content' in select_reg) and (re.match(select_reg['content'], article_data.get('content', '')) is None):
            continue
        message_list.append({'title': user_name + '：' + article_data.get('title', ''),
                             'content': article_data.get('content', ''), 'url': article.get('url', '')})
    if diff or (len(old_weibo_list) > 10 * (page_num + 1)):
        write_history_file('weibo_' + str(user_name) + '.txt', old_weibo_list, 10 * (page_num + 1), delta_days)
    return {'status': 0, 'data': message_list}
