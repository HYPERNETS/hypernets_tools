#!/usr/bin/python3.9

from ctypes import CDLL
from os.path import abspath
from subprocess import Popen, PIPE

from logging import debug


class RainSensor(object):
    def __init__(self):
        # FIXME :
        self.module = CDLL(abspath('hypernets/rain_sensor/rain_sensor_module.so')) # noqa
        # self.module = CDLL("rain_sensor_module.so")

        if self.module.check_gpio_access() < 0:  # If no write access to GPIO
            del self.module
        else:
            self.module.configure_gpio_port()

    def read_value(self):

        value = -1
        if hasattr(self, 'module'):
            value = self.module.read_value()
        else:
            read_command = ["./hypernets/rain_sensor/rain_sensor", "--python"]
            return_value = Popen(read_command, stdout=PIPE)
            value = int(return_value.stdout.read())
        return value

    def __del__(self):
        if hasattr(self, 'module'):
            debug("Releasing GPIO port")
            self.module.release_gpio_port()


if __name__ == '__main__':
    rain_sensor = RainSensor()
