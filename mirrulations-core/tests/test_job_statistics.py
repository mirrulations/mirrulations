from mirrcore.jobs_statistics import JobStatistics
from mirrmock.mock_redis import MockRedisWithStorage


def test_set_regulations_data_counts():
    job_stats = JobStatistics(MockRedisWithStorage())

    data = [1, 2, 3]
    job_stats.set_regulations_data(data)

    results = job_stats.get_data_totals()

    assert results['regulations_total_dockets'] == 1
    assert results['regulations_total_documents'] == 2
    assert results['regulations_total_comments'] == 3


def test_get_bucket_size():
    job_stats = JobStatistics(MockRedisWithStorage())
    job_stats.set_bucket_size(10)
    assert job_stats.get_bucket_size() == 10


def test_buckey_key_does_not_exist():
    job_stats = JobStatistics(MockRedisWithStorage())
    assert job_stats.get_bucket_size() == 0


def test_get_jobs_done_and_increase_jobs_done():
    cache = MockRedisWithStorage()
    stats = JobStatistics(cache)
    stats.increase_jobs_done('dockets')
    stats.increase_jobs_done('documents')
    stats.increase_jobs_done('comments')
    stats.increase_jobs_done('attachment', is_pdf=False)
    stats.increase_jobs_done('attachment', is_pdf=True)

    done = stats.get_jobs_done()
    assert done['num_jobs_done'] == 3
    assert done['num_dockets_done'] == 1
    assert done['num_documents_done'] == 1
    assert done['num_comments_done'] == 1
    assert done['num_attachments_done'] == 2
    assert done['num_pdf_attachments_done'] == 1
