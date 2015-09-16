import socket
import os


def is_raspberrypi():
    return os.uname()[4].startswith('arm')


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 80))
    return s.getsockname()[0]
