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
            chip_path = "gpiochip7"
            RAIN_SENSOR_LINE = 4

            self.chip = gpiod.Chip(chip_path)

            # We are assuming that the F81866A gets initialised first
            # and other GPIO chips, e.g. the FTDI usb-serial chip
            # after that. However, we must check it to make sure that
            # we are not messing with the wrong GPIO line!
            #
            # For additional safety udev adds rw permissions only to gpiochip7. 
            # We can't open chip using the label since probing the labels
            # needs access to all the gpiochip* devices.
            if self.chip.label() != "gpio-f7188x-7":
                raise Exception(f"it is the wrong chip!")

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
