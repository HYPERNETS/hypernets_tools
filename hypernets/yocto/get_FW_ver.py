from time import sleep
from html import unescape
from urllib.request import urlopen
from urllib.error import HTTPError
from logging import error

from hypernets.yocto.init import get_url_base_prefixed, get_url_base, get_url_gps


def get_module_FW_ver(url_base):
    get = "/".join(["api", "module", "productName"])
    url = "/".join([url_base, get])
    name = urlopen(url).read()
    get = "/".join(["api", "module", "firmwareRelease"])
    url = "/".join([url_base, get])
    fw = urlopen(url).read()
    return tuple([unescape(name.decode("utf-8")), unescape(fw.decode("utf-8"))])


def get_FW_ver():
    values = list()

    try:
        for url_base in [get_url_base(), get_url_base_prefixed(), get_url_gps()]:
            values.append((get_module_FW_ver(url_base)))

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module is not online")
        else:           
            error(f"HTTP Error: {e.code}")

    except Exception as e:
        error(f"{e}")
    
    # return only unique values
    return list(set(values))


if __name__ == "__main__":
    out="Yocto firmware versions: "
    for i in get_FW_ver():
        out += f"{i[0]} = {i[1]}, "

    print(out.rstrip(", "))
