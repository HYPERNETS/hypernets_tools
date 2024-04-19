from time import sleep
from hypernets.yocto.init import init, get_url_base_prefixed, get_url_base, get_url_gps

from html import unescape
from urllib.request import urlopen

def get_FW_ver():
    config = init()

    url_base = get_url_base_prefixed()

    def get_module_FW_ver(url_base):
        get = "/".join(["api", "module", "productName"])
        url = "/".join([url_base, get])
        name = urlopen(url).read()
        get = "/".join(["api", "module", "firmwareRelease"])
        url = "/".join([url_base, get])
        fw = urlopen(url).read()
        return tuple([unescape(name.decode("utf-8")), unescape(fw.decode("utf-8"))])

    values = list()
    for url_base in [get_url_base(), get_url_base_prefixed(), get_url_gps()]:
        values.append((get_module_FW_ver(url_base)))

    return values

if __name__ == "__main__":
    out="Yocto firmware versions: "
    for i in get_FW_ver():
        out += f"{i[0]} = {i[1]}, "

    print(out.rstrip(", "))
