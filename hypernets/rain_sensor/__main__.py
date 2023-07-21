
from logging import basicConfig, debug, info, DEBUG, INFO  # noqa
from hypernets.rain_sensor.rain_sensor_python import RainSensor
from time import sleep

if __name__ == '__main__':
    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%Y-%m-%dT%H:%M:%S'
    basicConfig(level=DEBUG, format=log_fmt, datefmt=dt_fmt)
    rain_sensor = RainSensor()
    for i in range(10):
        info(f"Read value : {rain_sensor.read_value()}")
        sleep(1)
