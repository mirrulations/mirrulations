from collections import Counter
import datetime
import pytz

class ResultsProcessor:

    def __init__(self, job_queue, data_storage):
        self.job_queue = job_queue
        self.data_storage = data_storage

    def get_time(self):
        # Get the current time in UTC
        utc_time = datetime.datetime.utcnow()

        # Convert the UTC time to Eastern Time
        eastern_timezone = pytz.timezone('US/Eastern')
        eastern_time = utc_time.astimezone(eastern_timezone)

        # Return the Eastern Time as a string
        return eastern_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    def process_results(self, results_dict):
        counts = Counter()
        for item in results_dict['data']:
            # data_storage.exists(), this seems to be taking long. by the time the it gets to add_job() 
            # the connection is lost. 

            # should the if check be taking this long
            if not self.data_storage.exists(item):
                # sets url and job_type
                url = item['links']['self']
                job_type = item['type']
                # adds current job to jobs_waiting_queue
                self.job_queue.add_job(url, job_type)
                print("\nresults processor: ADDED job to waiting queue")
                counts[job_type] += 1
                if job_type == 'comments':
                    # updates the url and job_type
                    url = url + '/attachments'
                    # adds new attachment job to jobs_waiting_queue
                    reg_id = item['id']
                    agency = reg_id.split('-')[0]
                    print("adding attachment job")
                    self.job_queue.add_job(url, 'attachments', reg_id, agency)
                    counts['attachment'] += 1
            else:
                counts['preexisting'] += 1

        print_report(counts)


def print_report(counts):
    # join counts into a single string
    report = ', '.join([f'{key}: {counts[key]}' for key in counts])
    print(f'Added {report}')
