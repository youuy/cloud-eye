import requests


def check(url, response_check):
    response = requests.get(url, timeout=(2, 2))
    if response.status_code == 200 and response_check in response.text:
        return True
    else:
        print("check result is err: {}, {}" % response.status_code, response.text)
        return False
