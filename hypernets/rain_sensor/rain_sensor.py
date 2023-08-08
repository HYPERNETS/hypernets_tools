#!/usr/bin/python3

import gpiod
from logging import debug, error


class RainSensor(object):
    def __init__(self):
        try: 
            # Cincoze DE-1000 has Super I/O chip F81866A
            # Digital Inputs are GPIO74...GPIO77
            # Digital Outputs are GPIO80...GPIO83
            # Rain sensor is connected to first DI GPIO74
            # Udev rules find the correct gpiochip and link /dev/rain_sensor to it
            chip_path = "/dev/rain_sensor"
            RAIN_SENSOR_LINE = 4
            self.chip = gpiod.Chip(chip_path)

        except Exception as e:
            error(f"Failed to open GPIO chip {chip_path}: {e}")
            raise e

        debug("Configuring GPIO port")
        self.line = self.chip.get_line(RAIN_SENSOR_LINE)
        self.line.request(consumer="hypstar", type=gpiod.LINE_REQ_DIR_IN)


    def read_value(self):
        debug("Reading value...")
        return self.line.get_value()


    def __del__(self):
        try:
            self.line.release()
            self.chip.close()
            debug("Releasing GPIO port")
        except AttributeError as e:
            pass
