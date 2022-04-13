#  from argparse import ArgumentParser
from hypernets.yocto.init import init, get_url_base
from yoctopuce.yocto_api import YAPI
# from configparser import ConfigParser
# from yoctopuce.yocto_wakeupmonitor import YWakeUpMonitor

# from logging import debug


if __name__ == '__main__':
    config = init()
    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        from urllib.request import urlopen
        url_base = "/".join([get_url_base(), "api", "dualPower", "extVoltage"])
        # print(url_base + get)
        # url = urlopen(url_base + get)
        url = urlopen(url_base)
        voltage = int(url.read()) / 1000
        print(voltage)

    else:
        # yocto_prefix = config["yoctopuce"]["yocto_prefix0"]
        print("Not implemented")

    YAPI.FreeAPI()
