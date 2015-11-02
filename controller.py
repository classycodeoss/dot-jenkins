#!/usr/bin/env python
import sys
import getopt
import json
import logging
import time
import requests.exceptions
import importlib
import datetime
import threading

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
        self.view_refresh_interval = config_json.get('viewRefreshInterval', 30)
        logging.info("Using view refresh interval: %d", self.view_refresh_interval)
        self.view_refresh_error_interval = config_json.get('viewRefreshErrorInterval', 60)
        logging.info("Using view refresh error interval: %d", self.view_refresh_interval)
        self.ssl_verify_certificates = config_json.get('sslVerifyCertificates', True)
        if not self.ssl_verify_certificates:
            logging.warn("SSL certificate validation disabled via config")
            requests.packages.urllib3.disable_warnings()  # requests uses a bundled urllib3 module
        self.network_interface_name = config_json.get('networkInterfaceName', None)
        self.display_update_interval = config_json.get('displayUpdateInterval', 5.0)
        self.delta_time_step = config_json.get('deltaTimeStep', 10)
        self.username = config_json.get('username', None)
        self.auth_token = config_json.get('authToken', None)


class ViewState(object):
    def __init__(self, view):
        self.view = view
        self.failed_index = None


class RenderThread(threading.Thread):
    def __init__(self, gadget, update_interval, delta_time_step):
        super(RenderThread, self).__init__()
        self.setDaemon(True)
        self.__view_state = None
        self.gadget = gadget
        self.update_interval = update_interval
        self.delta_time_step = delta_time_step

    def run(self):
        while True:
            time.sleep(self.update_interval)
            view_state = self.acquire_view_state()
            if view_state is None:
                self.render_no_data()
            else:
                self.render(view_state)

    def acquire_view_state(self):
        """Fetch view state"""
        return self.__view_state # reading instance variable is atomic in Python

    def set_view_state(self, view_state):
        self.__view_state = view_state # writing instance variable is atomic in Python

    def render(self, view_state):
        if view_state.failed_index is None:
            self.display_overview(view_state.view)
            if view_state.view.num_failing_jobs > 0:
                view_state.failed_index = 0 # start displaying first failed job at next tick
        else:
            failed_jobs = view_state.view.failing_jobs()
            self.display_failed_job(failed_jobs[view_state.failed_index])
            if view_state.failed_index < len(failed_jobs) - 1:
                view_state.failed_index += 1 # display next failed job at next tick
            else:
                view_state.failed_index = None # go back to overview at next tick

    def display_overview(self, view):
        lines = [
            view.name,
            'S/U/F: %d/%d/%d' % (view.num_succeeding_jobs, view.num_unstable_jobs, view.num_failing_jobs),
            self.get_last_updated_str(view.last_update)
        ]
        self.gadget.set_status_lines(lines)

        # set mood depending on failed/unstable/successful jobs
        if view.num_failing_jobs > 0:
            self.gadget.set_background_status(gadget.BackgroundStatus.Error)
            self.gadget.set_indicator(0, gadget.IndicatorStatus.Off)
            self.gadget.set_indicator(1, gadget.IndicatorStatus.Off)
            self.gadget.set_indicator(2, gadget.IndicatorStatus.On)
        elif view.num_unstable_jobs > 0:
            self.gadget.set_background_status(gadget.BackgroundStatus.Warn)
            self.gadget.set_indicator(0, gadget.IndicatorStatus.Off)
            self.gadget.set_indicator(1, gadget.IndicatorStatus.On)
            self.gadget.set_indicator(2, gadget.IndicatorStatus.On)
        else:
            self.gadget.set_background_status(gadget.BackgroundStatus.Ok)
            self.gadget.set_indicator(0, gadget.IndicatorStatus.On)
            self.gadget.set_indicator(1, gadget.IndicatorStatus.On)
            self.gadget.set_indicator(2, gadget.IndicatorStatus.On)

    def display_failed_job(self, job_and_build):
        job, build = job_and_build
        if len(job.display_name) > gadget.MAX_CHARS:
            line1 = job.display_name[:gadget.MAX_CHARS]
            line2 = '..' + job.display_name[gadget.MAX_CHARS:]
        else:
            line1 = job.display_name
            line2 = ''
        lines = [
            'Job Failed:',
            line1, line2
        ]
        self.gadget.set_status_lines(lines)

    def get_last_updated_str(self, last_update):
        now_datetime = datetime.datetime.now()
        timedelta = now_datetime - last_update
        dt_seconds = timedelta.seconds
        if dt_seconds < self.delta_time_step:
            return "Just now!"
        else:
            # count up in 30 second intervals (default) to be less busy
            return "%d seconds ago" % ((timedelta.seconds/self.delta_time_step)*self.delta_time_step)

    def render_no_data(self):
        self.gadget.set_background_status(gadget.BackgroundStatus.Info)
        self.gadget.set_status_lines([
            'No data yet',
            'Please wait...',
            'Refresh pending'
        ])


class Controller(object):
    def __init__(self, config):
        self.config = config
        if sysutils.is_raspberrypi():
            self.gadget = importlib.import_module('dothatgadget').DotHatGadget()
        else:
            logging.warn('Not running on RaspberryPi, using dummy hardware')
            self.gadget = gadget.GadgetBase()
        logging.info("Instantiated gadget: %s", type(self.gadget))
        self.render_thread = RenderThread(self.gadget, config.display_update_interval, config.delta_time_step)

    def run_blocking(self):
        self.render_thread.start()
        while True:
            view = jenkins.View(self.config.view_url, username=self.config.username, auth_token=self.config.auth_token,
                                ssl_verify_certificates=self.config.ssl_verify_certificates)
            try:
                view.refresh()
            except requests.exceptions.RequestException as e:
                logging.error("Failed to refresh view, will try again later: %s", e.message)
                time.sleep(self.config.view_refresh_error_interval)
                continue
            except ValueError as e:
                logging.error("Failed to refresh view, will try again later: %s", e.message)
                time.sleep(self.config.view_refresh_error_interval)
                continue

            # update the rendering thread's view state
            self.render_thread.set_view_state(ViewState(view))

            # and sleep until the next iteration
            time.sleep(self.config.view_refresh_interval)

    def display_system_infos(self):
        lines = [
            'Version: %s' % __version__,
            sysutils.get_ip_address(),
            'Getting ready...'
        ]
        self.gadget.set_status_lines(lines)
        self.gadget.display_boot_animation()


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

    logging.basicConfig(stream=sys.stdout, level=logging.WARN,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='YYYY-MM-DDTHH:mm:ss.SSSZ')
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    controller = Controller(config)
    controller.display_system_infos()
    time.sleep(10)
    controller.run_blocking()
