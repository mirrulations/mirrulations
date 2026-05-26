from collections import Counter

REGULATIONS_API_BASE = 'https://api.regulations.gov/v4'


def job_url_from_listing_item(item):
    """Build a detail-job URL from a search/listing result item."""
    url = f'{REGULATIONS_API_BASE}/{item["type"]}/{item["id"]}'
    if item['type'] == 'comments':
        url = f'{url}?include=attachments'
    return url


class ResultsProcessor:

    def __init__(self, job_queue):
        self.job_queue = job_queue

    def process_results(self, results_dict):
        counts = Counter()
        for item in results_dict['data']:
            url = job_url_from_listing_item(item)
            job_type = item['type']
            # adds current job to jobs_waiting_queue
            self.job_queue.add_job(url, job_type)
            counts[job_type] += 1
        print_report(counts)


def print_report(counts):
    # join counts into a single string
    report = ', '.join([f'{key}: {counts[key]}' for key in counts])
    print(f'Added {report}')
