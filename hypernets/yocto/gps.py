from hypernets.yocto.init import get_url_gps

from logging import debug


def get_gps(return_float=True):
    from urllib.request import urlopen
    url_base = get_url_gps()

    get = "/".join(["api", "gps", "dateTime"])
    url = "/".join([url_base, get])
    datetime = urlopen(url).read()

    get = "/".join(["api", "latitude", "currentValue"])
    url = "/".join([url_base, get])
    latitude = float(urlopen(url).read()) / 1000

    get = "/".join(["api", "longitude", "currentValue"])
    url = "/".join([url_base, get])
    longitude = float(urlopen(url).read()) / 1000

    return latitude, longitude, datetime


if __name__ == "__main__":
    # TODO : Make CLI
    print(get_gps(return_float=True))
