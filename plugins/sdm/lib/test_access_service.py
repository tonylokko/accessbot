# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
import datetime
from datetime import timezone, timedelta
from unittest.mock import MagicMock
import pytest
import strongdm

from .access_service import AccessService

resource_id = 1
resource_name = "myresource"
account_id = 55
account_email = "myaccount@test.com"
grant_start_from = datetime.datetime.now(timezone.utc) + timedelta(minutes=1)
grant_valid_until = grant_start_from + timedelta(hours=1)

@pytest.fixture()
def client():
    return MagicMock()

@pytest.fixture()
def service(client):
    return AccessService(client)

class Test_get_resource_by_name:
    def test_when_resource_exists_returns_resource(self, client, service):
        client.resources.list = MagicMock(return_value = get_resource_list_iter())
        sdm_resource = service.get_resource_by_name(resource_name)
        assert sdm_resource.id == resource_id
        assert sdm_resource.name == resource_name

    def test_when_sdm_client_fails_raises_exception(self, client, service):
        error_message = "SDM Client failed"
        client.resources.list = MagicMock(side_effect = Exception(error_message))
        with pytest.raises(Exception) as ex:
            service.get_resource_by_name(resource_name)
        assert error_message in str(ex.value)

    def test_when_resource_doesnt_exist_raises_exception(self, client, service):
        client.resources.list = MagicMock(return_value = iter([]))
        with pytest.raises(Exception):
            service.get_resource_by_name(resource_name)

class Test_get_account_by_email:
    def test_when_account_exists_returns_account(self, client, service):
        client.accounts.list = MagicMock(return_value = self.get_account_list_iter())
        sdm_account = service.get_account_by_email(account_email)
        assert sdm_account.id == account_id
        assert sdm_account.email == account_email

    def test_when_sdm_client_fails_raises_exception(self, client, service):
        error_message = "SDM Client failed"
        client.accounts.list = MagicMock(side_effect = Exception(error_message))
        with pytest.raises(Exception) as ex:
            service.get_account_by_email(account_email)
        assert error_message in str(ex.value)

    def test_when_account_doesnt_exist_raises_exception(self, client, service):
        client.accounts.list = MagicMock(return_value = iter([]))
        with pytest.raises(Exception):
            service.get_account_by_email(account_email)

    @staticmethod
    def get_account_list_iter():
        mock_account = MagicMock()
        mock_account.id = account_id
        mock_account.email = account_email
        return iter([mock_account])

class Test_grant_temporary_access:
    def test_when_grant_is_possible(self, client, service):
        client.account_grants.create = MagicMock()
        service.grant_temporary_access(resource_id, account_id, grant_start_from, grant_valid_until)
        expected_sdm_grant = strongdm.AccountGrant(
            resource_id = resource_id,
            account_id = account_id,
            start_from = grant_start_from, 
            valid_until = grant_valid_until
        )
        actual_sdm_grant = client.account_grants.create.call_args[0][0]
        assert dir(expected_sdm_grant) == dir(actual_sdm_grant)

    def test_when_grant_is_not_possible(self, client, service):
        error_message = "Grant is not possible" # TODO Validate if it raises an exception
        client.account_grants.create = MagicMock(side_effect = Exception(error_message))
        with pytest.raises(Exception) as ex:
            service.grant_temporary_access(resource_id, account_id, grant_start_from, grant_valid_until)
        assert error_message in str(ex.value)

class Test_get_all_resources:
    def test_returns_resources(self, client, service):
        client.resources.list = MagicMock(return_value = get_resource_list_iter())
        sdm_resources = service.get_all_resources()
        assert len(sdm_resources) == 1
        assert sdm_resources[0].id == resource_id
        assert sdm_resources[0].name == resource_name


def get_resource_list_iter():
    mock_resource = MagicMock()
    mock_resource.id = resource_id
    mock_resource.name = resource_name
    return iter([mock_resource])
