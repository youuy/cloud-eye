import requests


def check(url, response_check):
    response = requests.get(url, timeout=(2, 2))
    return response.status_code == 200 and response_check in response.text
