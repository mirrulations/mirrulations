import datetime
import json
import pytz


class MockDataSet:

    def __init__(self, num_results, job_type='dockets',
                 start_date='2020-01-01 00:00:00'):
        utc = pytz.utc

        self.start = datetime.datetime.fromisoformat(start_date)\
            .replace(tzinfo=utc)
        self.delta = datetime.timedelta(seconds=1)
        self.counter = 1
        self.num_results = num_results
        self.results = []
        self.type = job_type

    def get_results(self):

        while self.num_results > 5000:
            self.make_full_pages_of_results(count=20,
                                            total_count=self.num_results)
            self.num_results -= 5000
        self.make_full_pages_of_results(count=self.num_results // 250,
                                        total_count=self.num_results)
        self.num_results -= (self.num_results // 250) * 250
        self.make_partial_page_of_results(result_count=self.num_results,
                                          total_count=650)

        return self.results

    def make_item(self):
        attributes = {
            'lastModifiedDate': (
                (self.start + self.delta * self.counter).strftime(
                    '%Y-%m-%dT%H:%M:%SZ'))
        }
        links = {
            'self': f'http://a.b.c/{self.counter}'
        }
        relationships = {
            "attachments": {
                "links": {
                    "self": "api_attachment_url",
                    "related": "api_attachment_url"
                }
            }
        }
        return {
            'id': f'ABC-2020-{self.counter}',
            'attributes': attributes,
            'type': self.type,
            'links': links,
            'relationships': relationships
        }

    def make_full_pages_of_results(self, count, total_count):
        for result_count in range(1, count + 1):
            data = []
            for _ in range(250):
                data.append(self.make_item())
                self.counter += 1
            meta = {
                'totalElements': total_count,
                'pageNumber': result_count,
                'totalPages': 20
            }

            self.results.append(
                {'text': json.dumps({'data': data, 'meta': meta})})

    def make_partial_page_of_results(self, result_count, total_count):
        data = []
        for _ in range(result_count):
            data.append(self.make_item())
            self.counter += 1
        meta = {
            'totalElements': total_count,
            'pageNumber': 3,
            'totalPages': 3
        }

        self.results.append({'text': json.dumps({'data': data, 'meta': meta})})
