import requests
import json
import re
from urllib import parse
import time
from datetime import datetime, timedelta
from history_file import *
from log_err import *
requests.packages.urllib3.disable_warnings()


def query_weibo_content(weibo_id):
    retry = 3
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
            return {'status': 0, 'title': title, 'content': weibo_content}
        except Exception as e:
            retry = retry - 1
            if retry == 0:
                log_err({'err_module': 'query_notice_content', 'err_info': str(e),
                         'err_content': 'URL:' + 'https://m.weibo.cn/statuses/extend?id=' + str(weibo_id) +
                                        ' content:' + req.text})
                return {'status': -1, 'err_info': str(e), 'err_content': 'URL:' +
                        'https://m.weibo.cn/statuses/extend?id=' + str(weibo_id) + ' content:' + req.text}


def query_weibo_list(suffix):
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
    while retry > 0:
        try:
            req = requests.get(url, headers=headers, verify=False)
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
                         'err_content': 'URL:' + url + ' content:' + req.text})
                return {'status': -1, 'err_info': str(e),
                        'err_content': 'URL:' + url + ' content:' + req.text}
    try:
        weibo_id_list = []
        for card in weibo_list['data']['cards']:
            if (card.get('card_type') != 9) or ('mblog' not in card) or ('scheme' not in card):
                continue
            try:
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
                 'err_content': 'URL:' + url + ' content:' + req.text})
        return {'status': -1, 'err_info': str(e),
                'err_content': 'URL:' + url + ' content:' + req.text}


def check_weibo_update(first, suffix, user_name, page_num, page_turn_type, select_reg={}):
    weibo_list = []
    current_result = query_weibo_list(suffix)
    if current_result['status'] != 0:
        return {'status': -1}
    weibo_list += current_result['data']
    if page_turn_type == 0:
        since_id = current_result['since']
        count = 1
        while (count < page_num) and (since_id != ''):
            current_result = query_weibo_list(suffix + '&since_id=' + str(since_id))
            if current_result['status'] != 0:
                return {'status': -1}
            weibo_list += current_result['data']
            since_id = current_result['since']
            count += 1
    if page_turn_type == 1:
        for page_no in range(1, page_num):
            current_result = query_weibo_list(suffix + '&page=' + str(page_no + 1))
            if current_result['status'] != 0:
                return {'status': -1}
            weibo_list += current_result['data']
    # print(weibo_list)
    if first:
        write_history_file('weibo_' + str(user_name) + '.txt', weibo_list, 'hash')
        return {'status': 0, 'data': []}

    old_weibo_list = load_history_file('weibo_' + str(user_name) + '.txt')
    # print(old_weibo_list)
    diff = []
    for weibo in weibo_list:
        if weibo.get('hash', '') == '':
            continue
        if str(weibo['hash']) not in old_weibo_list:
            diff.append(weibo)
    # print(diff)

    message_list = []
    for article in diff:
        article_data = query_weibo_content(article['id'])
        if article_data['status'] != 0:
            weibo_list.remove(article)
            continue
        if ('title' in select_reg) and (re.match(select_reg['title'], article_data.get('title', '')) is None):
            continue
        if ('content' in select_reg) and (re.match(select_reg['content'], article_data.get('content', '')) is None):
            continue
        message_list.append({'title': user_name + '：' + article_data.get('title', ''),
                             'content': article_data.get('content', ''), 'url': article.get('url', '')})
    write_history_file('weibo_' + str(user_name) + '.txt', weibo_list, 'hash')
    return {'status': 0, 'data': message_list}