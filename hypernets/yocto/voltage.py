from hypernets.yocto.init import get_url_base


if __name__ == '__main__':
    from urllib.request import urlopen
    url_base = "/".join([get_url_base(), "api", "dualPower", "extVoltage"])
    # print(url_base + get)
    # url = urlopen(url_base + get)
    url = urlopen(url_base)
    voltage = int(url.read()) / 1000
    print(voltage)

