import pytest
import tempfile
import os
from mirrextractor.extractor import Extractor
from mirrmock.mock_redis import MockRedisWithStorage
from mirrcore.jobs_statistics import JobStatistics
import redis


def test_extract_text_pdf_disabled(capfd, mocker):
    """Test that PDF extraction is disabled and creates a stub file."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        Extractor.extract_text('test.pdf', temp_path)
        captured = capfd.readouterr()
        assert "PDF extraction disabled" in captured[0]
        
        # Check that file was created with disabled message
        assert os.path.exists(temp_path)
        with open(temp_path, 'r') as f:
            content = f.read()
        assert "PDF extraction disabled" in content
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_init_job_statistics(mocker):
    """Test that job statistics initialization works."""
    mocker.patch('redis.Redis', return_value=MockRedisWithStorage())
    Extractor.init_job_stat()
    assert hasattr(Extractor, 'job_stat')


def test_update_stats_success(mocker):
    """Test that update stats works without error."""
    job_stat = JobStatistics(MockRedisWithStorage())
    Extractor.job_stat = job_stat
    Extractor.update_stats()
    # Should increment extractions counter
    assert job_stat.get_jobs_done()['num_extractions_done'] == 1


def test_redis_connection_error(mocker, capfd):
    """Test that Redis connection errors are handled gracefully."""
    job_stat = JobStatistics(MockRedisWithStorage())
    Extractor.job_stat = job_stat
    Extractor.job_stat.increase_extractions_done = \
        mocker.Mock(side_effect=redis.ConnectionError("Connection failed"))
    Extractor.update_stats()
    captured = capfd.readouterr()
    assert "Couldn't increase extraction cache number due to:" in captured[0]
    assert "Connection failed" in captured[0]
