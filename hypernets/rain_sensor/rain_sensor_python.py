#!/usr/bin/python3.9

from ctypes import CDLL
# from ctypes import *
from os import path


_rain_sensor_module = CDLL(path.abspath('rain_sensor_module.so'))

# _rain_sensor_module.configure_gpio_port.argtypes = ()

_rain_sensor_module.check_gpio_access()
_rain_sensor_module.configure_gpio_port()
v = _rain_sensor_module.read_value()
_rain_sensor_module.release_gpio_port()
print(v)
