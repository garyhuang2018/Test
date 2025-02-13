#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Date  : 2024-09-09 15:33
@Author  : lxx
@Site  : http://192.192.0.118:3000/linxuxin/GemvaryTools
@File  : index.py
@Description  : 
"""
import json
from typing import List

from src.api.index import get_api_key

import requests


def login(url, params):
    """
    登录请求接口
    :param url:
    :param params:
    :return:
    """
    response = requests.post(url=f"{url}/system/login?account={params[0]}&password={params[1]}")
    result = response.json()
    print(result)
    cookies_result = response.cookies.items()[0]

    if result['code'] == "000000":
        return f"{cookies_result[0]}={cookies_result[1]}"
    else:
        return ""


def hotel_login(url, params):
    """
    登录请求接口
    :param url:
    :param params:
    :return:
    """
    headers = {"Content-Type": "application/json", "Host": ""}
    response = requests.post(url=f"{url}/sysprojectUser/login", json=params, headers=headers)
    result = response.json()
    print(result)
    cookies_result = response.cookies.items()[0]
    if result['code'] == 200:
        print(f"{cookies_result[0]}={cookies_result[1]}")
        return f"{cookies_result[0]}={cookies_result[1]}"
    else:
        return ""


def iot_login(url, params):

    headers = {"X-API-KEY": get_api_key("POST", "/auth/admin/login")}

    response = requests.post(url=f"{url}/api/auth/admin/login", json=params,  headers=headers)

    result = response.json()

    print(result)

    return result


if __name__ == '__main__':
    IotProdServerUrl = "https://iotadmin.gemvary.cn"
    IotProdUserName = "15989760200"
    IotProdPassword = "888888"
    iot_request_data = {
        "type": "password",
        "username": "15989760200",
        "password": "888888"
    }
    iot_login(IotProdServerUrl, iot_request_data)