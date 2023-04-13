from mirrextractor.extractor import Extractor
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


def test_text_extraction_throws_error(mocker, capfd):
    mocker.patch('pikepdf.open', return_value=pikepdf.Pdf.new())
    mocker.patch('pikepdf.Pdf.save', return_value=None)
    mocker.patch('pdfminer.high_level.extract_text', side_effect=ValueError)
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "FAILURE: failed to extract text from" in capfd.readouterr()[0]


def test_extract_pdf(mocker, capfd):
    mocker.patch('pikepdf.open', return_value=pikepdf.Pdf.new())
    mocker.patch('pikepdf.Pdf.save', return_value=None)
    mocker.patch('pdfminer.high_level.extract_text', return_value='test')
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch("builtins.open", mocker.mock_open())
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "SUCCESS: Saved extraction at" in capfd.readouterr()[0]
