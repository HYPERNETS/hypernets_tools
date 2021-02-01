from time import sleep
from hypernets.scripts.yocto_init import init

from yoctopuce.yocto_api import YAPI
from yoctopuce.yocto_temperature import YTemperature
from yoctopuce.yocto_humidity import YHumidity
from yoctopuce.yocto_pressure import YPressure
from yoctopuce.yocto_lightsensor import YLightSensor


def get_meteo(count=1, interval=1, print_value=False):

    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_prefix1"]

    temperature = YTemperature.FindTemperature(yocto_prefix + '.temperature')
    humidity = YHumidity.FindHumidity(yocto_prefix + '.humidity')
    pressure = YPressure.FindPressure(yocto_prefix + '.pressure')
    light = YLightSensor.FindLightSensor(yocto_prefix + '.lightSensor')

    sensors = [temperature, humidity, pressure, light]

    values = list()
    for _ in range(count):
        sleep(interval)
        for sensor in sensors:
            if sensor.isOnline():
                current = tuple([sensor.get_currentValue(), sensor.get_unit()])
                values.append(current)
                if print_value:
                    print(current)

    YAPI.FreeAPI()
    return values


if __name__ == "__main__":
    # TODO : make CLI
    # print(get_meteo(count=1000, interval=.5, print_value=True))
    print(get_meteo())
