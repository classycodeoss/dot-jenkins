#!/usr/bin/env python
import sys
import getopt
import json
import logging
import time
import os
import requests.exceptions
import importlib
import datetime

import jenkins
import gadget

__version__ = '1.0.0'


def is_raspberrypi():
    return os.uname()[4].startswith("arm")


class Configuration(object):

    def __init__(self, path_to_config):
        logging.info("Reading configuration from path: %s" % path_to_config)
        config_fd = open(path_to_config)
        config_json = json.load(config_fd)
        config_fd.close()
        self.view_url = config_json['viewUrl']
        logging.info("Using view at: %s", self.view_url)
        self.view_refresh_interval = config_json.get('viewRefreshInterval', 10)
        logging.info("Using view refresh interval: %d", self.view_refresh_interval)
        self.view_refresh_error_interval = config_json.get('viewRefreshErrorInterval', 60)
        logging.info("Using view refresh error interval: %d", self.view_refresh_interval)
        self.ssl_verify_certificates = config_json.get('sslVerifyCertificates', True)
        if not self.ssl_verify_certificates:
            logging.warn("SSL certificate validation disabled via config")
            requests.packages.urllib3.disable_warnings()  # requests uses a bundled urllib3 module


class Controller(object):
    def __init__(self, config):
        self.config = config
        if is_raspberrypi():
            self.gadget = importlib.import_module('dothatgadget').DotHatGadget()
        else:
            logging.warn('Not running on RaspberryPi, using dummy hardware')
            self.gadget = gadget.GadgetBase()
        logging.info("Instantiated gadget: %s", type(self.gadget))

    def run_blocking(self):
        view = jenkins.View(self.config.view_url, ssl_verify_certificates=self.config.ssl_verify_certificates)
        while True:
            try:
                view.refresh()
            except requests.exceptions.RequestException as e:
                logging.error("Failed to refresh view, will try again later: %s", e.message)
                time.sleep(self.config.view_refresh_error_interval)
                continue

            self.dislay_view_overview(view)
            # loop over the jobs

            time.sleep(self.config.view_refresh_interval)

    def dislay_view_overview(self, view):
        lines = [
            view.name,
            'S/F/T: %d/%d/%d' % (view.num_succeeding_jobs, view.num_failing_jobs, view.num_jobs),
            self.get_last_updated_str(view.last_update)
        ]
        self.gadget.set_status_lines(lines)

        # update LED indicators for the first 6 jobs in the view
        for i in range(len(view.jobs)):
            job = view.jobs[i]
            last_build = view.last_build_for_job.get(job.url, None)
            if last_build is None:
                self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)
            else:
                if last_build.result == jenkins.BuildResult.Success:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.On)
                elif last_build.result == jenkins.BuildResult.Unstable:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.On)
                elif last_build.result == jenkins.BuildResult.Failure:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)
                elif last_build.result == jenkins.BuildResult.Unstable:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)

    def get_last_updated_str(self, last_update):
        timedelta = datetime.datetime.now() - last_update
        return "%d seconds ago" % timedelta.total_seconds()




def print_usage():
    print("Usage: controller.py -c PATH_TO_CONFIGURATION [-p http://proxyhost:port]")


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.WARN)

    options, remainder = getopt.getopt(sys.argv[1:], 'c:p:', ['config=', 'proxy='])
    config = None
    for o, a in options:
        if o in ('-c', '--config'):
            config = Configuration(a)

    if config is None:
        print_usage()
        sys.exit(1)

    Controller(config).run_blocking()
