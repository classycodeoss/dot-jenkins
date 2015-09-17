#!/usr/bin/env python
import sys
import getopt
import json
import logging
import time
import requests.exceptions
import importlib
import datetime

import jenkins
import gadget
import sysutils

__version__ = '1.0.0'


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
        self.network_interface_name = config_json.get('networkInterfaceName', None)


class Controller(object):
    def __init__(self, config):
        self.config = config
        if sysutils.is_raspberrypi():
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
                self.display_error(e)
                logging.error("Failed to refresh view, will try again later: %s", e.message)
                time.sleep(self.config.view_refresh_error_interval)
                continue
            except ValueError as e:
                self.display_error(e)
                logging.error("Failed to refresh view, will try again later: %s", e.message)
                time.sleep(self.config.view_refresh_error_interval)
                continue

            self.dislay_view_overview(view)
            # loop over the jobs

            time.sleep(self.config.view_refresh_interval)

    def display_error(self, e):
        self.gadget.set_background_status(gadget.BackgroundStatus.Error)
        self.gadget.set_status_lines([
            'Error encountered',
            'while fetching.',
            'Will try later.'
        ])

    def display_system_infos(self):
        lines = [
            'Version: %s' % __version__,
            sysutils.get_ip_address(),
            'Getting ready...'
        ]
        self.gadget.set_status_lines(lines)
        self.gadget.display_boot_animation()

    def dislay_view_overview(self, view):
        lines = [
            view.name,
            'S/U/F: %d/%d/%d' % (view.num_succeeding_jobs, view.num_unstable_jobs, view.num_failing_jobs),
            self.get_last_updated_str(view.last_update)
        ]
        self.gadget.set_status_lines(lines)

        # set mood depending on failed/unstable/successful jobs
        if view.num_failing_jobs > 0:
            self.gadget.set_background_status(gadget.BackgroundStatus.Error)
        elif view.num_unstable_jobs > 0:
            self.gadget.set_background_status(gadget.BackgroundStatus.Warn)
        else:
            self.gadget.set_background_status(gadget.BackgroundStatus.Ok)

        # update LED indicators for the first 6 jobs in the view
        self.gadget.clear_build_indicators()
        for i in range(len(view.jobs)):
            job = view.jobs[i]
            last_build = view.last_build_for_job.get(job.url, None)
            if last_build is None:
                self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)
            else:
                if last_build.result == jenkins.BuildResult.Success:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.On)
                elif last_build.result == jenkins.BuildResult.Unstable:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)
                elif last_build.result == jenkins.BuildResult.Unstable:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)
                else:
                    self.gadget.set_build_indicator(i, gadget.IndicatorStatus.Off)

    def get_last_updated_str(self, last_update):
        now_datetime = datetime.datetime.now()
        #timedelta = now_datetime - last_update
        # TODO: as soon as we refresh constantly, show something like '5 seconds ago...'
        return "@ %s" % now_datetime.strftime('%H:%M:%S')


def print_usage():
    print("Usage: controller.py -c PATH_TO_CONFIGURATION [--debug]")


if __name__ == '__main__':
    debug = False
    options, remainder = getopt.getopt(sys.argv[1:], 'c:', ['config=', 'debug'])
    config = None
    for o, a in options:
        if o in ('-c', '--config'):
            config = Configuration(a)
        elif o == '--debug':
            debug = True

    if config is None:
        print_usage()
        sys.exit(1)

    logging.basicConfig(stream=sys.stdout, level=logging.WARN)
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    controller = Controller(config)
    controller.display_system_infos()
    time.sleep(10)
    controller.run_blocking()
