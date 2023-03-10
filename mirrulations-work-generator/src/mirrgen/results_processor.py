from collections import Counter


class ResultsProcessor:

    def __init__(self, job_queue, data_storage):
        self.job_queue = job_queue
        self.data_storage = data_storage

    def process_results(self, results_dict):
        counts = Counter()
        for item in results_dict['data']:
            if not self.data_storage.exists(item):
                # sets url and job_type
                url = item['links']['self']
                job_type = item['type']
                # adds current job to jobs_waiting_queue
                self.job_queue.add_job(url, job_type)
                counts[job_type] += 1
                if job_type == 'comments':
                    # updates the url and job_type
                    url = url + '/attachments'
                    # adds new attachment job to jobs_waiting_queue
                    reg_id = item['id']
                    agency = reg_id.split('-')[0]
                    self.job_queue.add_job(url, 'attachments', reg_id, agency)
                    counts['attachment'] += 1
            else:
                counts['preexisting'] += 1

        print_report(counts)


def print_report(counts):
    # join counts into a single string
    report = ', '.join([f'{key}: {counts[key]}' for key in counts])
    print(f'Added {report}')
