from mirrserver.get_client_id_validator import GetClientIDValidator
from mirrserver.get_client_id_validator import InvalidClientIDException
import pytest


def test_get_client_id_with_non_numerical_client_id():
    validator = GetClientIDValidator()
    client_id = 'a'
    with pytest.raises(InvalidClientIDException):
        validator.check_get_client_id(client_id)


def test_get_client_id_valid_client_id():
    validator = GetClientIDValidator()
    client_id = '10'
    assert validator.check_get_client_id(client_id)


def test_get_client_id_client_id_is_null():
    validator = GetClientIDValidator()
    client_id = None
    assert validator.check_get_client_id(client_id)
