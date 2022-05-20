import requests
import time
import uuid
import hashlib
import base64
import logging


def buildWSSEHeader(appKey, appSecret):
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ')  # Created
    nonce = str(uuid.uuid4()).replace('-', '')  # Nonce
    digest = hashlib.sha256((nonce + now + appSecret).encode()).hexdigest()

    digestBase64 = base64.b64encode(digest.encode()).decode()  # PasswordDigest
    return 'UsernameToken Username="{}",PasswordDigest="{}",Nonce="{}",Created="{}"'.format(appKey, digestBase64, nonce,
                                                                                            now)


def notify(content, config):
    logging.debug("wechat_bot_notify(%s)" % content)
    # 请求Headers
    header = {'Authorization': 'WSSE realm="SDP",profile="UsernameToken",type="Appkey"',
              'X-WSSE': buildWSSEHeader(config.get('app_key'), config.get('app_secret'))}
    # 请求Body

    template_paras = '["%s", "%s","%s"]' % (content[1][0:20], content[2][0:20], content[3][0:20])
    logging.debug("template_paras: %s" % template_paras)
    form_data = {'from': config.get('sender'),
                 'to': config.get('receiver'),
                 'templateId': config.get('template_id'),
                 'templateParas': template_paras,
                 'signature': config.get('signature')
                 }
    # 为防止因HTTPS证书认证失败造成API调用失败,需要先忽略证书信任问题
    response = requests.post(config.get('url'), data=form_data, headers=header, verify=False)
    logging.debug(response.text)
    return response.status_code and response.json().get('code') == '000000'
