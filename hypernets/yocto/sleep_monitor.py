#  from argparse import ArgumentParser
from hypernets.yocto.init import init
from yoctopuce.yocto_api import YAPI
from configparser import ConfigParser
from yoctopuce.yocto_wakeupmonitor import YWakeUpMonitor


if __name__ == '__main__':
    config = init()
    config_dynamic = ConfigParser()
    config_dynamic.read("config_dynamic.ini")
    if config_dynamic["general"]["keep_pc"] == "off":
        yocto_prefix = config["yoctopuce"]["yocto_prefix2"]
        monitor = YWakeUpMonitor.FindWakeUpMonitor(yocto_prefix +
                                                   ".wakeUpMonitor")
        monitor.set_sleepCountdown(10)
    YAPI.FreeAPI()
