from collections import Counter


class ResultsProcessor:

    def __init__(self, job_queue):
        self.job_queue = job_queue

    def process_results(self, results_dict):
        counts = Counter()
        for item in results_dict['data']:
            url = item['links']['self']
            job_type = item['type']
            if job_type == 'comments':
                # updates the url and job_type
                url = url + '?include=attachments'
            # adds current job to jobs_waiting_queue
            self.job_queue.add_job(url, job_type)
            counts[job_type] += 1
        print_report(counts)


def print_report(counts):
    # join counts into a single string
    report = ', '.join([f'{key}: {counts[key]}' for key in counts])
    print(f'Added {report}')
