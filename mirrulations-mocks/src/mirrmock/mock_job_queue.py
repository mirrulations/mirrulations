# pylint: disable=unused-argument
class MockJobQueue:

    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)

    def get_num_jobs(self):
        return len(self.jobs)

    def get_job(self):
        return self.jobs[0]

    def decrement_count(self, job):
        return self.jobs.pop(0)
