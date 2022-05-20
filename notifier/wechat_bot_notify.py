import logging

import requests


def notify(content, config):
    logging.debug("wechat_bot_notify(%s)" % content)
    result = True
    for url in config.get('url'):
        try:
            request_body = {"msgtype": "markdown",
                            "markdown": {"content": "监控告警：%s %s ，%s：%s" % (content[0], content[1], content[2], content[3])}}
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=request_body)
            logging.debug(response.text)
            if response.status_code != 200 or response.json().get('errcode') != 0:
                result = False
        except:
            logging.error("wechat_bot_notify通知失败%s" % url)
    return result
