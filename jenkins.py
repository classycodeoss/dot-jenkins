import requests
import logging
import datetime

class BuildResult:
    Failure, Unstable, Success, NotBuilt, Other = range(5)


class Build(object):

    def __init__(self, json_obj):
        self.display_name = json_obj['displayName']

        if json_obj['result'] == 'SUCCESS':
            self.result = BuildResult.Success
        elif json_obj['result'] == 'FAILURE':
            self.result = BuildResult.Failure
        elif json_obj['result'] == 'UNSTABLE':
            self.result = BuildResult.Unstable
        elif json_obj['result'] == 'NOT_BUILT':
            self.result = BuildResult.NotBuilt
        else:
            self.result = BuildResult.Other
        self.number = json_obj['number']
        self.timestamp = json_obj['timestamp']


class Job(object):

    def __init__(self, json_obj, fetch_last_build=True):
        self.display_name = json_obj['displayName']
        self.url = json_obj['url']
        self.color = json_obj['color']

        health_report = json_obj['healthReport']
        if len(health_report) > 0:
            self.build_health_text = health_report[0]['description']
            self.build_health_score = health_report[0]['score']
        else:
            self.build_health_text = None
            self.build_health_score = None

        if len(health_report) > 1:
            self.test_health_text = health_report[1]['description']
            self.test_health_score = health_report[1]['score']
        else:
            self.test_health_text = None
            self.test_health_score = None

        if json_obj['lastCompletedBuild'] is not None:
            self.last_build_url = json_obj['lastCompletedBuild']['url']
            self.last_build_number = json_obj['lastCompletedBuild']['number']
        else:
            self.last_build_url = None
            self.last_build_number = None


class View(object):

    def __init__(self, url, username=None, auth_token=None, ssl_verify_certificates=True):
        self.url = url
        self.name = None
        self.jobs = None
        self.num_failing_jobs = -1
        self.num_jobs = -1
        self.num_succeeding_jobs = -1
        self.num_unstable_jobs = -1
        self.last_build_for_job = None
        self.ssl_verify_certificates = ssl_verify_certificates
        self.last_update = None
        self.username = username
        self.auth_token = auth_token

    def refresh(self):
        sess = requests.Session()
        if self.username is not None and self.auth_token is not None:
            sess.auth = (self.username, self.auth_token)

        # first, fetch the view itself, and obtain the list of job references
        logging.info('Fetching view from URL: ' + self.url)
        resp_json = sess.get(self.url, verify=self.ssl_verify_certificates).json()
        job_urls = [obj['url'] for obj in resp_json['jobs']]
        self.name = resp_json['name']

        # now fetch all jobs in the view
        logging.info('Fetching Jobs from URLs: ' + str(job_urls))
        self.jobs = [Job(sess.get(url + 'api/json', verify=self.ssl_verify_certificates).json()) for url in job_urls]

        self.last_build_for_job = {}
        for job in self.jobs:
            if job.last_build_url is not None:
                self.last_build_for_job[job.url] = Build(sess.get(job.last_build_url + 'api/json', verify=self.ssl_verify_certificates).json())

        self.num_jobs = len(self.jobs)
        self.num_succeeding_jobs = len(self.succeeding_jobs())
        self.num_failing_jobs = len(self.failing_jobs())
        self.num_unstable_jobs = len(self.unstable_jobs())
        self.last_update = datetime.datetime.now()

    def failing_jobs(self):
        return filter(lambda x: x[1] is not None and x[1].result == BuildResult.Failure,
                      [(job, self.last_build_for_job.get(job.url, None)) for job in self.jobs])

    def unstable_jobs(self):
        return filter(lambda x: x[1] is not None and (x[1].result == BuildResult.Unstable or x[1].result == BuildResult.NotBuilt),
                      [(job, self.last_build_for_job.get(job.url, None)) for job in self.jobs])

    def succeeding_jobs(self):
        return filter(lambda x: x[1] is not None and x[1].result == BuildResult.Success,
                      [(job, self.last_build_for_job.get(job.url, None)) for job in self.jobs])
