from mirrextractor.extractor import Extractor
from mirrmock.mock_redis import MockRedisWithStorage
from mirrcore.jobs_statistics import JobStatistics
import pikepdf
import redis
import boto3
from moto import mock_s3


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


def test_init_job_statistics(mocker):
    mocker.patch('redis.Redis', return_value=MockRedisWithStorage())
    Extractor.init_job_stat()


@mock_s3
def test_redis_connection_error(mocker, capfd):
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="mirrulations")
    mocker.patch('pikepdf.open', return_value=pikepdf.Pdf.new())
    mocker.patch('pikepdf.Pdf.save', return_value=None)
    mocker.patch('pdfminer.high_level.extract_text', return_value='test')
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch("builtins.open", mocker.mock_open())
    job_stat = JobStatistics(MockRedisWithStorage())
    Extractor.job_stat = job_stat
    Extractor.job_stat.increase_extractions_done = \
        mocker.Mock(side_effect=redis.ConnectionError)
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "Coudn't increase extraction cache number due to:" \
        in capfd.readouterr()[0]
    assert job_stat.get_jobs_done()['num_extractions_done'] == 0


@mock_s3
def test_extract_pdf(mocker, capfd):
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="mirrulations")
    mocker.patch('pikepdf.open', return_value=pikepdf.Pdf.new())
    mocker.patch('pikepdf.Pdf.save', return_value=None)
    mocker.patch('pdfminer.high_level.extract_text', return_value='test')
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch("builtins.open", mocker.mock_open())
    job_stat = JobStatistics(MockRedisWithStorage())
    Extractor.job_stat = job_stat
    Extractor.extract_text('a.pdf', 'b.txt')
    assert "SUCCESS: Saved extraction at" in capfd.readouterr()[0]
    assert job_stat.get_jobs_done()['num_extractions_done'] == 1
