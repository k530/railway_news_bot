from datetime import datetime, timedelta
import time
import re
from log_err import *


def format_weibo_datetime(datestr):
    now = datetime.now()
    ymd = now.strftime("%Y-%m-%d")
    y = now.strftime("%Y")
    newstr = datestr
    newdate = datetime.strptime('2000-01-01', '%Y-%m-%d')
    try:
        if u"楼" in datestr:
            newstr = datestr.split(u"楼")[-1].strip()
        if u"今天" in newstr:
            mdate = time.mktime(time.strptime(ymd + newstr, '%Y-%m-%d今天 %H:%M'))
            newdate = datetime.fromtimestamp(mdate)
        elif u"月" in newstr:
            mdate = time.mktime(time.strptime(y + newstr, '%Y%m月%d日 %H:%M'))
            newdate = datetime.fromtimestamp(mdate)
        elif u"分钟前" in newstr:
            newdate = now - timedelta(minutes=int(newstr[:-3]))
        elif u"秒前" in newstr:
            newdate = now - timedelta(minutes=int(newstr[:-2]))
        elif re.match(r'[1-9]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])', newstr):
            mdate = time.mktime(time.strptime(newstr, '%Y-%m-%d'))
            newdate = datetime.fromtimestamp(mdate)
        elif re.match(r'(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])', newstr):
            mdate = time.mktime(time.strptime(y + "-" + newstr, '%Y-%m-%d'))
            newdate = datetime.fromtimestamp(mdate)
        elif u"昨天" in newstr:
            mdate = time.mktime(time.strptime(ymd + newstr, '%Y-%m-%d昨天 %H:%M'))
            newdate = datetime.fromtimestamp(mdate) - timedelta(days=1)
        elif u"小时前" in newstr:
            newdate = now - timedelta(hours=int(newstr[:-3]))
        elif u"+0800" in newstr:
            newdate = datetime.strptime(newstr, "%a %b %d %H:%M:%S +0800 %Y")
        else:
            newdate = datetime.strptime(newstr, "%Y-%m-%d %H:%M")
    except Exception as e:
        log_err({'err_module': 'format_weibo_datetime', 'err_info': str(e),
                 'err_content': datestr})
    return newdate
