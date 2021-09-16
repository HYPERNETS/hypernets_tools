from hypernets.yocto.init import init, get_url_gps

from yoctopuce.yocto_api import YAPI
from yoctopuce.yocto_gps import YGps

from yoctopuce.yocto_latitude import YLatitude
from yoctopuce.yocto_longitude import YLongitude


def get_gps(print_value=True, return_float=True):
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        return _get_gps_usb(print_value, return_float)
    else:
        return _get_gps_ip(print_value, return_float)


def _get_gps_usb(print_value, return_float):
    from urllib.request import urlopen
    url_base = get_url_gps()

    get = "/".join(["api", "latitude", "currentValue"])
    url = "/".join([url_base, get])
    latitude = float(urlopen(url).read())

    get = "/".join(["api", "longitude", "currentValue"])
    url = "/".join([url_base, get])
    longitude = float(urlopen(url).read())

    get = "/".join(["api", "gps", "dateTime"])
    url = "/".join([url_base, get])
    datetime = urlopen(url).read()

    return latitude, longitude, datetime


def _get_gps_ip(print_value, return_float):
    config = init()
    yocto_prefix = config["yoctopuce"]["yocto_gps"]

    gps = YGps.FindGps(yocto_prefix + '.gps')
    values = list()

    if print_value or not return_float:
        values = f"Position : {gps.get_latitude()} {gps.get_longitude()}"\
            f"\nDatetime : {gps.get_dateTime()}"

        if print_value:
            print(values)

        if not return_float:
            return values

    values = list()
    latitude = YLatitude.FindLatitude(yocto_prefix + '.latitude')
    longitude = YLongitude.FindLongitude(yocto_prefix + '.longitude')

    if latitude.isOnline():
        values.append(latitude.get_currentValue()/1000)

    if longitude.isOnline():
        values.append(longitude.get_currentValue()/1000)

    if gps.isOnline():
        values.append(gps.get_dateTime())

    YAPI.FreeAPI()
    return values


if __name__ == "__main__":
    # TODO : Make CLI
    print(get_gps(print_value=True, return_float=True))
