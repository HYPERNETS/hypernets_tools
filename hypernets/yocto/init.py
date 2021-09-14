#!/usr/bin/python

from yoctopuce.yocto_api import YRefParam, YAPI
from configparser import ConfigParser
from sys import exit

yoctopuce_config_file = "config_static.ini"


def init():
    config = ConfigParser()
    config.read(yoctopuce_config_file)
    yoctopuce_ip = config["yoctopuce"]["yoctopuce_ip"]

    if yoctopuce_ip == "usb":
        return config

    errmsg = YRefParam()
    if YAPI.RegisterHub(yoctopuce_ip, errmsg) != YAPI.SUCCESS:
        exit("init error:" + errmsg.value)

    return config


def get_url_base():
    config = init()
    yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
    yocto_prefix1 = config["yoctopuce"]["yocto_prefix1"]
    return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                     yocto_prefix1])
