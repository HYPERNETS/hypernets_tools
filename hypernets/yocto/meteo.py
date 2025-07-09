from time import sleep
from html import unescape
from urllib.request import urlopen
from urllib.error import HTTPError
from logging import debug, error
from hypernets.yocto.init import get_url_base_prefixed, get_yocto_lower_board_serial


def get_value_and_unit(sensor):
    url_base = get_url_base_prefixed()
    
    get = "/".join(["api", sensor, "currentValue"])
    url = "/".join([url_base, get])
    value = float(urlopen(url).read())
    get = "/".join(["api", sensor, "unit"])
    url = "/".join([url_base, get])
    unit = urlopen(url).read()
    return tuple([value, unescape(unit.decode("utf-8"))])


def get_meteo(count=1, interval=1):
    values = list()

    try:
        for sensor in ["temperature", "humidity", "pressure", "lightSensor"]:
            values.append((get_value_and_unit(sensor)))
    
        debug(values)

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_lower_board_serial()}' is not online")
        else:           
            error(f"HTTP Error: {e.code}")

    except Exception as e:
        error(f"{e}")

    return values


if __name__ == "__main__":
    # TODO : make CLI
    print(get_meteo(count=1000, interval=.5))
