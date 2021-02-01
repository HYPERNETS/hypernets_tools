#  from argparse import ArgumentParser
from hypernets.scripts.yocto_init import init
from yoctopuce.yocto_api import YAPI
from yoctopuce.yocto_wakeupmonitor import YWakeUpMonitor


if __name__ == '__main__':
    config = init()
    if config["general"]["keep_pc"] == "off":
        yocto_prefix = config["yoctopuce"]["yocto_prefix2"]
        monitor = YWakeUpMonitor.FindWakeUpMonitor(yocto_prefix +
                                                   ".wakeUpMonitor")
        monitor.set_sleepCountdown(10)
    YAPI.FreeAPI()
