from mirrextractor.extractor import Extractor
from mirrmock.mock_data_storage import MockDataStorage
import pikepdf


def mock_pdf_extraction(mocker):
    mocker.patch.object(
        Extractor,
        '_extract_pdf',
        return_value=None
    )


def test_extract_text(capfd, mocker):
    mock_pdf_extraction(mocker)
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "Extracting text from a.pdf" in capfd.readouterr()[0]


def test_extract_text_non_pdf(capfd, mocker):
    mock_pdf_extraction(mocker)
    Extractor.extract_text('a.docx', 'b.txt')
    assert "FAILURE: attachment doesn't have appropriate extension a.docx" \
        in capfd.readouterr()[0]


def test_open_pdf_throws_pikepdf_error(mocker, capfd):
    mocker.patch('pikepdf.open', side_effect=pikepdf.PdfError)
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "FAILURE: failed to open" in capfd.readouterr()[0]


def test_save_pdf_throws_runtime_error(mocker, capfd):
    mocker.patch('pikepdf.open', return_value=pikepdf.Pdf.new())
    mocker.patch('pikepdf.Pdf.save', side_effect=RuntimeError)
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "FAILURE: failed to save" in capfd.readouterr()[0]


def test_extract_pdf(mocker, capfd):
    storage = MockDataStorage()
    mocker.patch('pikepdf.open', return_value=pikepdf.Pdf.new())
    mocker.patch('pikepdf.Pdf.save', return_value=None)
    mocker.patch('pdfminer.high_level.extract_text', return_value='test')
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch("builtins.open", mocker.mock_open())

    mocker.patch.object(Extractor, 'add_extraction_to_database',
                        side_effect=storage.add_extraction_to_database)

    Extractor.extract_text('a.pdf', 'b.txt')
    assert "SUCCESS: Saved extraction at" in capfd.readouterr()[0]
    assert len(storage.extractions) == 1


def test_add_extraction_to_database(mocker):
    mock_storage = mocker.Mock()
    mocker.patch.object(Extractor, 'storage', mock_storage)
    save_path = '/path/test.txt'
    text = 'foo'
    Extractor.add_extraction_to_database(save_path, text)
    assert mock_storage.add_extracted_text.called_once_with(
        {'filename': 'test.txt', 'extracted_text': text})
