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
