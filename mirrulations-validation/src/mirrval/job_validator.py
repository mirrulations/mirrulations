import os
import sys
import time
from collections import Counter
import json
from dotenv import load_dotenv
from mirrgen.search_iterator import SearchIterator
from mirrcore.regulations_api import RegulationsAPI
from mirrcore.path_generator import PathGenerator


class Validator:

    def __init__(self, api, path_gen):
        self.api = api
        self.path_gen = path_gen
        self.unfound_jobs = {}

    def download(self, endpoint):
        beginning_timestamp = '1990-01-01 00:00:00'
        counter = Counter()
        for result in SearchIterator(self.api, endpoint, beginning_timestamp):
            if result == {}:
                continue
            for res in result['data']:
                job_path = self.path_gen.get_path({'data': res})
                if_path_exist = os.path.exists(('/data/data'+job_path).strip())
                if not if_path_exist:
                    print(f"{res['id']} not in database, writing to file")
                    write_unfound_jobs(res, self.unfound_jobs)
                    time.sleep(3.6)
                    counter['Not_in_db'] += 1
                counter['Total_validated'] += 1
            print(f'Jobs not found in database: {counter["Not_in_db"]}')
            print(f'Total jobs validated: {counter["Total_validated"]}')


def write_unfound_jobs(res, unfound_jobs):
    if f"missing_{res['type']}" not in unfound_jobs:
        unfound_jobs[f"missing_{res['type']}"] = [res['links']['self']]
    else:
        if not check_for_missing_jobs(res):
            unfound_jobs[f"missing_{res['type']}"].append(
                        res['links']['self'])
    with open("/data/validator/unfound_jobs.json", "w+",
              encoding="utf-8") as outfile:
        json.dump(unfound_jobs, outfile, indent=4)


def check_for_missing_jobs(res):
    with open("/data/validator/unfound_jobs.json", "r",
              encoding="utf-8") as outfile:
        lines = outfile.readlines()
        for line in lines:
            if res['links']['self'] in line:
                return True
        return False


def generate_work(collection=None):
    # commented out for static analysis reasons since
    # the variable 'database' isn't being used.
    # database = load_redis()

    # Get API key
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api = RegulationsAPI(api_key)
    path_gen = PathGenerator()
    # Download using validator
    generator = Validator(api, path_gen)
    if not collection:
        generator.download('dockets')
        generator.download('documents')
        generator.download('comments')
    else:
        generator.download(collection)


if __name__ == '__main__':
    job_types = ('dockets', 'documents', 'comments')
    while True:
        # Start from last job type performed
        if len(sys.argv) > 1 and sys.argv[1] in job_types:
            generate_work(sys.argv[1])
        else:
            generate_work()
        print("Validator sleeping for 30 days...")
        time.sleep(60*60*24*30)
