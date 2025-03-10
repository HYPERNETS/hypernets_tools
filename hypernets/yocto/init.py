#!/usr/bin/python

from configparser import ConfigParser

yoctopuce_config_file = "config_static.ini"


def init():
    config = ConfigParser()
    config.read(yoctopuce_config_file)
    return config


def get_url_base():
    config = init()
    try:
        yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2])
    except KeyError:
        # host system V4 or newer
        yocto_prefix3 = config["yoctopuce"]["yocto_prefix3"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix3])


def get_url_base_prefixed():
    config = init()
    try:
        yocto_prefix1 = config["yoctopuce"]["yocto_prefix1"]
        yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                         yocto_prefix1])
    except KeyError:
        # host system V4 or newer
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix1])


def get_url_gps():
    config = init()
    try:
        yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
        yocto_gps = config["yoctopuce"]["yocto_gps"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                         yocto_gps])
    except KeyError:
        yocto_prefix3 = config["yoctopuce"]["yocto_prefix3"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix3])
