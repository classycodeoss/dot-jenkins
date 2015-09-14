import unittest
import jenkins
import logging
import sys


class MyTestCase(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    def check_view_has_data(self, view):
        self.assertIsNotNone(view.jobs)
        for job in view.jobs:
            self.assertIsNotNone(job.display_name)
            self.assertIsNotNone(job.url)

            last_build = view.last_build_for_job.get(job.url, None)
            if last_build is not None:
                self.assertIsNotNone(last_build.result)
                self.assertIsNotNone(last_build.number)
                self.assertIsNotNone(last_build.display_name)

        self.assertGreater(view.num_jobs, 0)
        self.assertLessEqual(view.num_succeeding_jobs, view.num_jobs)
        self.assertLessEqual(view.num_failing_jobs, view.num_jobs)

    def test_iam30_view_contains_jobs(self):
        view = jenkins.View('https://dev-jenkins.bluecare.local/view/iam30/api/json')
        view.refresh()
        self.check_view_has_data(view)

    def test_larnags_view_contains_jobs(self):
        view = jenkins.View('https://dev-jenkins.bluecare.local/view/larnags/api/json')
        view.refresh()
        self.check_view_has_data(view)

    def test_hinclient_view_contains_jobs(self):
        view = jenkins.View('https://dev-jenkins.bluecare.local/view/HIN%20Client/api/json')
        view.refresh()
        self.check_view_has_data(view)



if __name__ == '__main__':
    unittest.main()
