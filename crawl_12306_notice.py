import requests
from bs4 import BeautifulSoup
import json
import re
from urllib import parse
import time
from history_file import *
from log_err import *
requests.packages.urllib3.disable_warnings()


def format_html_content(content):
    content = content.replace('\n', '').replace('\r', '').replace(' ', '')
    content = content.replace('</div>', '@line@').replace('</p>', '@line@').replace('<br/>', '@line@')
    content = re.sub(r'<xml>.*?</xml>', '', content)
    content = re.sub(r'<style>.*?</style>', '', content)
    content = re.sub(r'<script>.*?</script>', '', content)
    content = re.sub(r'<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});', '', content)
    content = re.sub(r'[\r\n]+', '\n', content.replace('@line@', '\n'))
    return content


def query_notice_content(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                  'q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'www.12306.cn',
        'Referer': 'https://www.12306.cn/mormhweb/zxdt/index_zxdt.html',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.132 Safari/537.36'
    }
    # print(url)
    retry = 3
    while retry > 0:
        try:
            req = requests.get(url, headers=headers, verify=False)
            time.sleep(2)
            soup = BeautifulSoup(req.content, 'html.parser')
            content_box = soup.find('div', class_='article-box')
            title = content_box.h3.get_text()
            content = format_html_content(content_box.div.prettify())
            # print(content)
            return {'status': 0, 'title': title, 'content': content}
        except Exception as e:
            retry = retry - 1
            if retry == 0:
                log_err({'err_module': 'query_12306_notice_content', 'err_info': str(e),
                         'err_content': 'URL:' + url + ' content:' + req.text})
                return {'status': -1, 'err_info': str(e), 'err_content': 'URL:' + url + ' content:' + req.text}


def query_notice_list(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                  'q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'www.12306.cn',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.132 Safari/537.36'
    }
    # print(url)
    article_list = []
    retry = 3
    while retry > 0:
        try:
            req = requests.get(url, headers=headers, verify=False)
            time.sleep(2)
            soup = BeautifulSoup(req.content, 'html.parser')
            article_list = soup.find('div', id='newList').ul.find_all('a')
            break
        except Exception as e:
            retry = retry - 1
            if retry == 0:
                log_err({'err_module': 'query_12306_notice_list', 'err_info': str(e),
                         'err_content': 'URL:' + url + ' content:' + req.text})
                return {'status': -1, 'err_info': str(e), 'err_content': 'URL:' + url + ' content:' + req.text}
    try:
        result = []
        for article in article_list:
            result.append({'url': parse.urljoin(url, article['href']), 'title': article['title']})
        return {'status': 0, 'data': result}
    except Exception as e:
        log_err({'err_module': 'query_12306_notice_list', 'err_info': str(e),
                 'err_content': 'URL:' + url + ' content:' + req.text})
        return {'status': -1, 'err_info': str(e), 'err_content': 'URL:' + url + ' content:' + req.text}


def check_12306_notice_update(first):
    article_list = []
    current_result = query_notice_list('https://www.12306.cn/mormhweb/zxdt/index_zxdt.html')
    if current_result['status'] != 0:
        return {'status': -1}
    article_list += current_result['data']
    for count in range(1, 2):
        current_result = query_notice_list('https://www.12306.cn/mormhweb/zxdt/index_zxdt_' + str(count) + '.html')
        if current_result['status'] != 0:
            return {'status': -1}
        article_list += current_result['data']
    # print(article_list)
    if first:
        write_history_file('12306.txt', article_list, 'url')
        return {'status': 0, 'data': []}

    old_article_list = load_history_file('12306.txt')
    diff = []
    for article in article_list:
        if article.get('url', '') == '':
            continue
        if article['url'] not in old_article_list:
            diff.append(article)
    if diff:
        print('Old List: ', old_article_list)
        print('Diff: ', diff)
        write_history_file('12306.txt', article_list, 'url')

    message_list = []
    for article in diff:
        article_data = query_notice_content(article['url'])
        if article_data['status'] != 0:
            article_list.remove(article)
            continue
        message_list.append({'title': article_data.get('title', ''), 'content': article_data.get('content', ''),
                             'url': article['url']})
    return {'status': 0, 'data': message_list}
