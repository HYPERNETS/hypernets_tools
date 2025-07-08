from hypernets.yocto.init import get_url_gps
from urllib.request import urlopen
from urllib.error import HTTPError
from logging import debug, error


def get_gps(return_float=True):
    try:
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

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto gps is not online")
        else:
            error(f"HTTP Error: {e.code}")
        return None

    except Exception as e:
        error(f"{e}")
        return None

    return latitude, longitude, datetime


if __name__ == "__main__":
    # TODO : Make CLI
    print(get_gps(return_float=True))
