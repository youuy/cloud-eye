import os
import time

import urllib3
import yaml
import schedule
import checker.http_checker as http_checker
import notifier.wechat_bot_notify as wechat_bot_notify
import notifier.sms_notify as sms_notify
import logging

last_notify_time = {}
last_notify_err = {}

notifier_method = {
    'wechat_bot': wechat_bot_notify,
    'sms': sms_notify,
}


def get_config():
    try:
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper
    current_path = os.path.abspath(".")
    yaml_path = os.path.join(current_path, "config.yaml")
    file = open(yaml_path, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    return yaml.load(file_data, Loader)


def do_notify(notifier, content):
    for notify in notifier:
        try:
            if notify.get('type') and notifier_method.get(notify.get('type')):
                notify_result = notifier_method.get(notify.get('type')).notify(content, notify.get('config'))
                if notify_result:
                    logging.info("通知成功：%s" % notify.get('type'))
                else:
                    logging.info("通知失败：%s" % notify.get('type'))
            else:
                logging.info("通知失败：%s不存在" % notify.get('type'))
        except:
            logging.info("通知失败：%s" % notify.get('type'))


def do_check(checker):
    result = 0
    if checker is not None:
        for check in checker:
            if check.get('type') == 'http_check':
                try:
                    check_result = http_checker.check(check.get('url'), check.get('response_check'))
                    if not check_result:
                        result += 1
                except:
                    result += 1
    return result


def health_check(check_sites, notify_interval, default_notifier):
    global last_notify_err
    global last_notify_time
    now = time.time()
    logging.info("开始检测站点...")
    for site in check_sites:
        site_name = site['name']
        # 如果没有设置notifier，则使用默认
        if site.get('notifier') is None and default_notifier is not None:
            site['notifier'] = default_notifier
        # 站点检查
        result = do_check(site.get('checker'))
        # 设置默认值
        if last_notify_time.get(site_name) is None:
            last_notify_time[site_name] = 0
        if last_notify_err.get(site_name) is None:
            last_notify_err[site_name] = False
        # 检查结果处理s
        if result > 0:
            if now - last_notify_time.get(site_name) > notify_interval:
                # 如果检测站点不正常并且上次通知时间已超过10分钟，则重新通知
                logging.info("站点%s检测到异常。" % site_name)
                last_notify_err[site_name] = True
                last_notify_time[site_name] = now
                content = [
                    time.strftime("%Y-%m-%d", time.localtime(now)),
                    time.strftime("%H:%M:%S", time.localtime(now)),
                    "站点%s" % site_name,
                    "异常"
                ]
                do_notify(site.get('notifier'), content)
            else:
                logging.info("站点%s检测到异常，上次通知时间：%s，本次不通知。" % (
                    site_name, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_notify_time.get(site_name)))))
        elif result == 0:
            if last_notify_err.get(site_name):
                # 如果检测站点正常并且上次是异常的，则通知
                logging.info("站点%s恢复正常" % site_name)
                last_notify_err[site_name] = False
                last_notify_time[site_name] = 0
                content = [
                    time.strftime("%Y-%m-%d", time.localtime(now)),
                    time.strftime("%H:%M:%S", time.localtime(now)),
                    "站点%s" % site_name,
                    "恢复正常"
                ]
                do_notify(site.get('notifier'), content)
            else:
                logging.info("站点%s正常。无需处理" % site_name)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s : %(levelname)s  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    urllib3.disable_warnings()
    # 系统配置
    config = get_config().get('config')
    node = config.get('node')
    __check_interval = config.get('check_interval')
    __notify_interval = config.get('notify_interval')
    logging.info("当前检测节点为：%s，检测间隔为：%s，同一异常通知间隔为：%s" % (node, __check_interval, __notify_interval))
    # 检测的站点信息
    __check_sites = get_config().get('check_sites')
    # 默认通知方式
    __default_notifier = config.get('default_notifier')
    health_check(__check_sites, __notify_interval, __default_notifier)
    schedule.every(__check_interval).seconds.do(health_check, __check_sites, __notify_interval, __default_notifier)
    while True:
        schedule.run_pending()
