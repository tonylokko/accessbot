class ShowProfileHelper:
    def __init__(self, bot):
        self.__bot = bot
        self.__sdm_service = bot.get_sdm_service()

    def execute(self, message):
        sdm_account = self.__get_sdm_account(message)
        sdm_account_details = self.__get_sdm_account_details(sdm_account)
        message = f"{self.__bot.get_sender_nick(message.frm)}, here's your profile details:\n"
        message += self.__format_account_details(sdm_account_details)
        yield message

    def __get_sdm_account(self, message):
        sender_email = self.__bot.get_sender_email(message.frm)
        return self.__sdm_service.get_account_by_email(sender_email)

    def __get_sdm_account_details(self, sdm_account):
        details = [
            {'label': 'SDM email', 'value': sdm_account.email}
        ]
        if sdm_account.tags:
            tags_list = []
            for key in sdm_account.tags.keys():
                tags_list.append(f'{key}: {sdm_account.tags[key]}')
            if len(tags_list):
                details.append({'label': 'SDM account tags', 'value': tags_list})
        return details

    def __format_account_details(self, details):
        message = ''
        # values = [(item["value"] if isinstance(item["value"], list) else [item["value"]]) for item in details]
        for detail in details:
            message += f'- **{detail["label"]}**\n'
            if isinstance(detail["value"], list):
                for value in detail["value"]:
                    message += f'    - {value}\n'
                continue
            message += f'    - {detail["value"]}\n'
        return message
