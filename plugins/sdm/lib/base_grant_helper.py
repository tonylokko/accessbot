from abc import ABC, abstractmethod
from .exceptions import NotFoundException
from typing import Any
import shortuuid
from grant_request_type import GrantRequestType
from .util import fuzzy_match


class BaseGrantHelper(ABC):
    auto_approve_tag_key = 'AUTO_APPROVE_TAG'
    auto_approve_all_key = 'AUTO_APPROVE_ALL'

    def __init__(self, bot, sdm_service, admin_ids, object_name, grant_type, auto_approve_tag_key, auto_approve_all_key):
        self.__bot = bot
        self.__sdm_service = sdm_service
        self.__admin_ids = admin_ids
        self.__object_name = object_name
        self.__grant_type = grant_type
        self.__auto_approve_tag_key = auto_approve_tag_key
        self.__auto_approve_all_key = auto_approve_all_key

    def __grant_access(self, message, sdm_object, sdm_account, execution_id, request_id):
        sender_nick = self.__bot.get_sender_nick(message.frm)
        sender_email = sdm_account.email
        self.__bot.log.info("##SDM## %s GrantHelper.__grant_%s sender_nick: %s sender_email: %s", execution_id, self.__object_name, sender_nick, sender_email)
        self.__create_grant_request(message, sdm_object, sdm_account, self.__grant_type, request_id)
        if self.__needs_manual_approval(sdm_object) or self.__reached_max_auto_approve_uses(message.frm.person):
            yield from self.__notify_access_request_entered(sender_nick, sdm_object.name, request_id)
            self.__bot.log.debug("##SDM## %s GrantHelper.__grant_%s needs manual approval", execution_id, self.__object_name)
            return
        self.__bot.log.info("##SDM## %s GrantHelper.__grant_%s granting access", execution_id, self.__object_name)
        yield from self.__bot.get_approve_helper().approve(request_id, True)

    def __create_grant_request(self, message, sdm_object, sdm_account, grant_request_type, request_id):
        self.__bot.enter_grant_request(request_id, message, sdm_object, sdm_account, grant_request_type)

    def __needs_manual_approval(self, sdm_resource):
        tagged_resource = self.__bot.config[self.__auto_approve_tag_key] is not None
        if self.__grant_type == GrantRequestType.ACCESS_RESOURCE:
            tagged_resource = tagged_resource and self.__bot.config[self.__auto_approve_tag_key] in sdm_resource.tags
        return not self.__bot.config[self.__auto_approve_all_key] and not tagged_resource

    def __reached_max_auto_approve_uses(self, requester_id):
        max_auto_approve_uses = self.__bot.config['MAX_AUTO_APPROVE_USES']
        if not max_auto_approve_uses:
            return False
        auto_approve_uses = self.__bot.get_auto_approve_use(requester_id)
        return auto_approve_uses >= max_auto_approve_uses

    def __notify_access_request_entered(self, sender_nick, resource_name, request_id):
        team_admins = ", ".join(self.__bot.get_admins())
        yield f"Thanks {sender_nick}, that is a valid request. Let me check with the team admins: {team_admins}\n" + r"Your request id is \`" + request_id + r"\`"
        operation_desc = self.get_operation_desc()
        self.__notify_admins(r"Hey I have an " + operation_desc + r" request from USER \`" + sender_nick + r"\` for " + self.__object_name.upper() + r" \`" + resource_name + r"\`! To approve, enter: *yes " + request_id + r"**")

    def __notify_admins(self, message):
        admins_channel = self.__bot.config['ADMINS_CHANNEL']
        if admins_channel:
            self.__bot.send(self.__bot.build_identifier(admins_channel), message)
            return

        for admin_id in self.__admin_ids:
            self.__bot.send(admin_id, message)

    def __get_account(self, message):
        sender_email = self.__bot.get_sender_email(message.frm)
        return self.__sdm_service.get_account_by_email(sender_email)

    def __try_fuzzy_matching(self, execution_id, term_list, role_name):
        similar_result = fuzzy_match(term_list, role_name)
        if not similar_result:
            self.__bot.log.error("##SDM## %s GrantHelper.access_%s there are no similar %ss.", execution_id, self.__object_name, self.__object_name)
        else:
            self.__bot.log.error("##SDM## %s GrantHelper.access_%s similar role found: %s", execution_id, self.__object_name, str(similar_result))
            yield f"Did you mean \"{similar_result}\"?"

    def request_grant_access(self, message, searched_name):
        execution_id = shortuuid.ShortUUID().random(length=6)
        operation_desc = self.get_operation_desc()
        self.__bot.log.info("##SDM## %s GrantHelper.access_%s new %s request for resource_name: %s", execution_id, self.__object_name, operation_desc, searched_name)
        try:
            sdm_resource = self.get_item_by_name(searched_name, execution_id)
            sdm_account = self.__get_account(message)
            error_msg = self.has_permission(sdm_resource, sdm_account, searched_name)
            if error_msg:
                yield error_msg
                return
            request_id = self.generate_grant_request_id()
            yield from self.__grant_access(message, sdm_resource, sdm_account, execution_id, request_id)
        except NotFoundException as ex:
            self.__bot.log.error("##SDM## %s GrantHelper.access_%s %s request failed %s", execution_id, self.__object_name, operation_desc, str(ex))
            yield str(ex)
            objects = self.get_all_items()
            yield from self.__try_fuzzy_matching(execution_id, objects, searched_name)

    @staticmethod
    @abstractmethod
    def generate_grant_request_id():
        pass

    @abstractmethod
    def has_permission(self, sdm_object, sdm_account, searched_name) -> str:
        pass

    @abstractmethod
    def get_all_items(self) -> Any:
        pass

    @abstractmethod
    def get_item_by_name(self, name, execution_id = None) -> Any:
        pass

    @abstractmethod
    def get_operation_desc(self):
        pass