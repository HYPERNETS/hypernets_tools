from time import sleep
from hypernets.yocto.init import get_url_base_prefixed

from logging import debug


def get_meteo(count=1, interval=1):
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


if __name__ == "__main__":
    # TODO : make CLI
    print(get_meteo(count=1000, interval=.5))
