
from logging import basicConfig, debug, DEBUG
from hypernets.rain_sensor.rain_sensor_python import RainSensor

if __name__ == '__main__':
    basicConfig(level=DEBUG)
    rain_sensor = RainSensor()
    debug(rain_sensor.read_value())
