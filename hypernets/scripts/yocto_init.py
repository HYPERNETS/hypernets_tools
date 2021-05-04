#!/usr/bin/python

from yoctopuce.yocto_api import YRefParam, YAPI
from configparser import ConfigParser
from sys import exit

yoctopuce_config_file = "config_static.ini"

def init():
    config = ConfigParser()
    config.read(yoctopuce_config_file)
    yoctopuce_ip = config["yoctopuce"]["yoctopuce_ip"]

    errmsg = YRefParam()
    if YAPI.RegisterHub(yoctopuce_ip, errmsg) != YAPI.SUCCESS:
        exit("init error:" + errmsg.value)

    return config
