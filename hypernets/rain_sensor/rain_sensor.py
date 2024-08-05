#!/usr/bin/python3

from subprocess import Popen, PIPE
from logging import debug, error, getLogger, DEBUG


class RainSensor(object):

    def read_value(self):
        debug("Reading value...")

        value = -1
        logger = getLogger()
        if logger.level == DEBUG and logger.disabled is not True:
            loglevel = "-d"
        else:
            loglevel = ""

        try: 
            read_command = ["./hypernets/rain_sensor/rain_sensor", f"{loglevel}"]
            subproc = Popen(read_command, stdout=PIPE)
            subproc.wait()
            return_value = subproc.returncode
            debug(f"Rain sensor state is {return_value}")

        except Exception as e:
            error(f"Failed to read rain sensor state: {e}")
            raise e

        if return_value != 0 and return_value != 1:
            raise Exception(f"Failed to read rain sensor state ({return_value})")

        return return_value

