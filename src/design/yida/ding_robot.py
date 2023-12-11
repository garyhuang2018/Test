import requests
import json

import requests
import json


class DingTalkMessenger:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

    def send_text_message(self, content):
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": [],
                "isAtAll": False
            }
        }
        response = requests.post(self.webhook_url, headers=self.headers, data=json.dumps(data))
        return response.text


# Example usage
# webhook_url = "https://oapi.dingtalk.com/robot/send?access_token" \
#               "=408ea6ab6bea4eca07bfb4d6b52fa56df97b71007c9d454cff80b6072be84947 "
# messenger = DingTalkMessenger(webhook_url)
# message_content = input("Enter the message content: ")
# response = messenger.send_text_message(message_content)
# print(response)

# webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN"
#
# headers = {
#     'Content-Type': 'application/json; charset=utf-8'
# }
#
# content = input("Enter the message content: ")
#
# data = {
#     "msgtype": "text",
#     "text": {
#         "content": content
#     },
#     "at": {
#         "atMobiles": [],
#         "isAtAll": False
#     }
# }
