
from mirrmock.mock_document_count import create_mock_mongodb


def test_mock_document_count():
    mock_db = create_mock_mongodb(1, 2, 3, 4)

    assert mock_db['mirrulations']['dockets'].estimated_document_count() == 1
    assert mock_db['mirrulations']['documents'].estimated_document_count() == 2
    assert mock_db['mirrulations']['comments'].estimated_document_count() == 3
    assert mock_db['mirrulations']['attachments'] \
        .estimated_document_count() == 4
