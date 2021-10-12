from hypernets.yocto.init import init, get_url_base
from yoctopuce.yocto_api import YAPI
from configparser import ConfigParser
from yoctopuce.yocto_wakeupmonitor import YWakeUpMonitor


if __name__ == '__main__':
    config = init()
    config_dynamic = ConfigParser()

    if config["yoctopuce"]["yoctopuce_ip"] == "usb":
        # from urllib.request import urlopen
        url_base = "/".join([get_url_base(), "api", "wakeUpMonitor"])
        # get = "?sleepCountdown=10&."
        # # print(url_base + get)
        # url = urlopen(url_base + get)
        # # print(url.code)

    else:
        yocto_prefix = config["yoctopuce"]["yocto_prefix2"]
        monitor = YWakeUpMonitor.FindWakeUpMonitor(yocto_prefix +
                                                   ".wakeUpMonitor")

        id_wakeupreason = monitor.get_wakeUpReason()

        str_wakeupreason = \
            {monitor.WAKEUPREASON_ENDOFSLEEP: "endofsleep",
             monitor.WAKEUPREASON_EXTPOWER: "ext power",
             monitor.WAKEUPREASON_EXTSIG1: "ext sig1",
             monitor.WAKEUPREASON_INVALID: "invalid",
             monitor.WAKEUPREASON_SCHEDULE1: "schedule1",
             monitor.WAKEUPREASON_SCHEDULE2: "schedule2",
             monitor.WAKEUPREASON_USBPOWER: "usb power"}[id_wakeupreason]

        print(str_wakeupreason)

    YAPI.FreeAPI()
