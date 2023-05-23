from unittest.mock import MagicMock
from mirrcore.data_counts import DataCounts


def test_get_counts(mocker):
    api_key = "test"
    dockets_response = MagicMock()
    dockets_response.json.return_value = {"meta": {"totalElements": 500}}
    documents_response = MagicMock()
    documents_response.json.return_value = {
        "meta": {"totalElements": 1000}}
    comments_response = MagicMock()
    comments_response.json.return_value = {"meta": {"totalElements": 2500}}

    mocker.patch('time.sleep')
    mocker.patch('requests.get', side_effect=[
        dockets_response,
        documents_response,
        comments_response
        ])

    counts = DataCounts(api_key).get_counts()

    assert counts == [500, 1000, 2500]


def test__get_total_elements():
    response = {"meta": {"totalElements": 123}}

    total_elements = DataCounts(  # pylint: disable=W0212
        api_key="test")._DataCounts__get_total_elements(response)

    assert total_elements == 123
