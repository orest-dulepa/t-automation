from slack import WebClient
from libraries.common import log_message


class SlackBot:
    message_template: dict = {
            "channel": "",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            ""
                        ),
                    },
                }
            ],
        }
    reported_service_type: list = []
    members: list = []
    manager: str = '<@U5NDH4A82|Zack>'

    def __init__(self, slack_bot_token: str, channel: str):
        self.slack_bot_token = slack_bot_token
        self.slack_web_client = WebClient(token=slack_bot_token)
        self.channel: str = channel

        try:
            response = self.slack_web_client.users_list()
            if response.status_code == 200:
                self.members = response.data['members']
        except Exception as ex:
            log_message('Unable to get user list')
            log_message(str(ex))

    def send_message(self, text: str) -> None:
        print(text)
        self.slack_web_client.chat_postMessage(**self.generate_message(text))

    def send_message_service_type_not_found(self, customer_or_service_type: str) -> None:
        if customer_or_service_type.strip().lower() in self.reported_service_type:
            return
        self.reported_service_type.append(customer_or_service_type.strip().lower())
        self.send_message(f'{customer_or_service_type} not found on Quickbooks drop down')

    def generate_message(self, text: str) -> dict:
        message: dict = self.message_template

        message['channel'] = self.channel
        message['blocks'][0]['text']['text'] = text
        return message

    def get_user_tag(self, user_name: str) -> str:
        result: str = f'@{user_name}'

        for user in self.members:
            try:
                if user['deleted']:
                    continue
                if user_name.strip().lower().replace(' ', '') in str(user['real_name']).strip().lower().replace(' ', ''):
                    result = f'<@{user["id"]}|>'
                    break
            except Exception as ex:
                print(str(ex))

        return result
