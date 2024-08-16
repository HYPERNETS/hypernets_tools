#!/usr/bin/python

from configparser import ConfigParser

yoctopuce_config_file = "config_static.ini"


def init():
    config = ConfigParser()
    config.read(yoctopuce_config_file)
    return config


def get_url_base():
    config = init()
    yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
    return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2])


def get_url_base_prefixed():
    config = init()
    yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
    yocto_prefix1 = config["yoctopuce"]["yocto_prefix1"]
    return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                     yocto_prefix1])


def get_url_gps():
    config = init()
    yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
    yocto_gps = config["yoctopuce"]["yocto_gps"]
    return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                     yocto_gps])
