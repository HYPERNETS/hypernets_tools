from time import sleep
from hypernets.yocto.init import init, get_url_base_prefixed

from logging import debug


def get_meteo(count=1, interval=1):
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        return _get_meteo_usb(count, interval)
    else:
        return _get_meteo_ip(count, interval)


def _get_meteo_usb(count, interval):
    from html import unescape
    from urllib.request import urlopen
    url_base = get_url_base_prefixed()

    # TODO
    # get = "?ctx=&lowestValue=100.0"
    # get = "?ctx=&highestValue=0.0"

    def get_value_and_unit(sensor):
        get = "/".join(["api", sensor, "currentValue"])
        url = "/".join([url_base, get])
        value = float(urlopen(url).read())
        get = "/".join(["api", sensor, "unit"])
        url = "/".join([url_base, get])
        unit = urlopen(url).read()
        return tuple([value, unescape(unit.decode("utf-8"))])

    values = list()
    for sensor in ["temperature", "humidity", "pressure", "lightSensor"]:
        values.append((get_value_and_unit(sensor)))

    debug(values)
    return values


def _get_meteo_ip(count, interval):
    from yoctopuce.yocto_api import YAPI
    from yoctopuce.yocto_temperature import YTemperature
    from yoctopuce.yocto_humidity import YHumidity
    from yoctopuce.yocto_pressure import YPressure
    from yoctopuce.yocto_lightsensor import YLightSensor

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
                debug(current)

    YAPI.FreeAPI()
    return values


if __name__ == "__main__":
    # TODO : make CLI
    print(get_meteo(count=1000, interval=.5))
