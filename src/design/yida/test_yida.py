# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import time
from typing import List

from alibabacloud_dingtalk.yida_1_0.client import Client as dingtalkyida_1_0Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dingtalk.yida_1_0 import models as dingtalkyida__1__0_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


# -*- coding: utf-8 -*-


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> dingtalkyida_1_0Client:
        """
        使用 Token 初始化账号Client
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkyida_1_0Client(config)

    @staticmethod
    def main(
            args: List[str],
    ) -> None:
        current_timestamp = int(time.time())*1000
        print(current_timestamp)
        client = Sample.create_client()
        create_or_update_form_data_headers = dingtalkyida__1__0_models.CreateOrUpdateFormDataHeaders()
        create_or_update_form_data_headers.x_acs_dingtalk_access_token = 'ed2e20f9314031f591d92f0ffdfd722d'
        create_or_update_form_data_request = dingtalkyida__1__0_models.CreateOrUpdateFormDataRequest(
            system_token='8K866L81SQLC6Y7AAY9GU8DM0NVB2P5G929KLKZ1',
            form_uuid='FORM-1FB43750764C4CCAB285B64DFD7BBA577X0U',
            user_id='012925513539826268',
            search_condition='[{  "key": "textField_lmoac3lv",  "value": "P2",  "type": "TEXT",  "operator": "like",  "componentName": "TextField" }]',
            # search_condition = '[{"key": "imageField_lq24fuvp","value": "fileUpload/","type": "TEXT","operator": "like","componentName": "ImageField"}]',
            app_type='APP_LNLRJTFC3IMVKZUYQ97H',
            form_data_json=f'''{{"textField_lmoac3lv":"P4-D", "textField_lmoac3lu":"004", 
                           "radioField_lq3d1ocp":"工厂贝塔测试间", "radioField_lq3d1ocp_id":"工厂贝塔测试间","dateField_lmoac3lw":{current_timestamp},}}'''
        )
        try:
            client.create_or_update_form_data_with_options(create_or_update_form_data_request,
                                                           create_or_update_form_data_headers,
                                                           util_models.RuntimeOptions())
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                print(err.code, err.message)
                pass

    @staticmethod
    async def main_async(
            args: List[str],
    ) -> None:
        client = Sample.create_client()
        create_or_update_form_data_headers = dingtalkyida__1__0_models.CreateOrUpdateFormDataHeaders()
        create_or_update_form_data_headers.x_acs_dingtalk_access_token = 'ac639ef9bcc93a4b873c46c850f0bc90'
        create_or_update_form_data_request = dingtalkyida__1__0_models.CreateOrUpdateFormDataRequest(
            system_token='8K866L81SQLC6Y7AAY9GU8DM0NVB2P5G929KLKZ1',
            form_uuid='FORM-1FB43750764C4CCAB285B64DFD7BBA577X0U',
            user_id='012925513539826268',
            search_condition='[{  "key": "textField_lmoac3lv",  "value": "cba",  "type": "TEXT",  "operator": "like",  "componentName": "TextField" }]',
            app_type='APP_LNLRJTFC3IMVKZUYQ97H',
            form_data_json='{"textField_lmoac3lv":"fire the hole"}'
        )
        try:
            await client.create_or_update_form_data_with_options_async(create_or_update_form_data_request,
                                                                       create_or_update_form_data_headers,
                                                                       util_models.RuntimeOptions())
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                pass


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
