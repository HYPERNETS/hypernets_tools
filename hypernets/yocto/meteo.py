from time import sleep
from hypernets.yocto.init import init, get_url_base


def get_meteo(count=1, interval=1, print_value=False):
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        return _get_meteo_usb(count, interval, print_value)
    else:
        return _get_meteo_ip(count, interval, print_value)


def _get_meteo_usb(count, interval, print_value):
    from urllib.request import urlopen
    get_url_base, urlopen

    url_base = get_url_base()

    # TODO
    # get = "?scr=&ctx=&lowestValue=100.0"
    # get = "?scr=&ctx=&highestValue=0.0"

    def get_value_and_unit(sensor):
        get = "/".join(["api", sensor, "currentValue"])
        url = "/".join([url_base, get])
        value = float(urlopen(url).read())
        get = "/".join(["api", sensor, "unit"])
        url = "/".join([url_base, get])
        unit = urlopen(url).read()
        return tuple([value, unit])

    values = list()
    for sensor in ["temperature", "humidity", "pressure", "lightSensor"]:
        values.append(get_value_and_unit(sensor))

    return values


def _get_meteo_ip(count, interval, print_value):
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
                if print_value:
                    print(current)

    YAPI.FreeAPI()
    return values


if __name__ == "__main__":
    # TODO : make CLI
    # print(get_meteo(count=1000, interval=.5, print_value=True))
    print(get_meteo())
