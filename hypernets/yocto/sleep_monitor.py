#  from argparse import ArgumentParser
from hypernets.yocto.init import init, get_url_base
from yoctopuce.yocto_api import YAPI
from configparser import ConfigParser
from yoctopuce.yocto_wakeupmonitor import YWakeUpMonitor

from logging import debug


if __name__ == '__main__':
    config = init()
    config_dynamic = ConfigParser()
    config_dynamic.read("config_dynamic.ini")

    if config_dynamic["general"]["keep_pc"] == "off":
        if config["yoctopuce"]["yoctopuce_ip"] == "usb":
            from urllib.request import urlopen
            url_base = "/".join([get_url_base(), "api", "wakeUpMonitor"])
            get = "?sleepCountdown=10&."
            # print(url_base + get)
            url = urlopen(url_base + get)
            # print(url.code)

        else:
            yocto_prefix = config["yoctopuce"]["yocto_prefix2"]
            monitor = YWakeUpMonitor.FindWakeUpMonitor(yocto_prefix +
                                                       ".wakeUpMonitor")
            monitor.set_sleepCountdown(10)

    YAPI.FreeAPI()
