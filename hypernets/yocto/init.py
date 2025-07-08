#!/usr/bin/python

from configparser import ConfigParser
from urllib.request import urlopen
from urllib.error import HTTPError
from logging import error

yoctopuce_config_file = "config_static.ini"


def init():
    config = ConfigParser()
    config.read(yoctopuce_config_file)

    ## add yoctopuce.generation parameter
    ## generation 1 - Yocto-Pictor-Wifi, host system V1-V3
    ## generation 2 - Yocto-Pictor-GPS, host system V4 or newer
    if config.has_option("yoctopuce", "yocto_prefix2"):
        config.set("yoctopuce", "generation", "1")
    elif config.has_option("yoctopuce", "yocto_prefix3"):
        config.set("yoctopuce", "generation", "2")
    else:
        if not config.has_section("yoctopuce"):
            raise Exception(f"Missing 'yoctopuce' configuration in {yoctopuce_config_file}!")
        else:
            raise Exception(f"No 'yocto_prefix2' or 'yocto_prefix3' in {yoctopuce_config_file}!")

    return config


def get_url_base():
    config = init()
    yocto_gen = config["yoctopuce"]["generation"]

    if yocto_gen == "1":
        # host system V1-V3 with Yocto-Pictor-Wifi
        yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2])
    elif yocto_gen == "2":
        # host system V4 or newer with Yocto-Pictor-GPS
        yocto_prefix3 = config["yoctopuce"]["yocto_prefix3"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix3])
    else:
        raise Exception(f"Yoctopuce generation {yocto_gen} is not supported!")


def get_url_base_prefixed():
    config = init()

    if not config.has_option("yoctopuce", "yocto_prefix1"):
        raise Exception(f"No 'yocto_prefix1' in {yoctopuce_config_file}!")

    yocto_gen = config["yoctopuce"]["generation"]
    yocto_prefix1 = config["yoctopuce"]["yocto_prefix1"]

    if yocto_gen == "1":
        # host system V1-V3 with Yocto-Pictor-Wifi
        yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                         yocto_prefix1])
    elif yocto_gen == "2":
        # host system V4 or newer with Yocto-Pictor-GPS
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix1])
    else:
        raise Exception(f"Yoctopuce generation {yocto_gen} is not supported!")


def get_url_gps():
    config = init()
    yocto_gen = config["yoctopuce"]["generation"]

    if yocto_gen == "1":
        try:
            yocto_prefix2 = config["yoctopuce"]["yocto_prefix2"]
            yocto_gps = config["yoctopuce"]["yocto_gps"]
            return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix2,
                             yocto_gps])
        except KeyError as e:
            raise Exception(f"No {e} in {yoctopuce_config_file} for generation {yocto_gen} Yocto!")

    elif yocto_gen == "2":
        yocto_prefix3 = config["yoctopuce"]["yocto_prefix3"]
        return "/".join(["http://127.0.0.1:4444/bySerial", yocto_prefix3])
    else:
        raise Exception(f"Yoctopuce generation {yocto_gen} is not supported!")


def get_yocto_gen():
    config = init()
    return config["yoctopuce"]["generation"]


def get_yocto_upper_board_serial():
    config = init()
    yocto_gen = config["yoctopuce"]["generation"]
    
    if yocto_gen == "1":
        sn = config["yoctopuce"]["yocto_prefix2"]
    elif yocto_gen == "2":
        sn = config["yoctopuce"]["yocto_prefix3"]
    else:
        raise Exception(f"Yoctopuce generation {yocto_gen} is not supported!")

    return sn


def get_yocto_lower_board_serial():
    config = init()
    return config["yoctopuce"]["yocto_prefix1"]
    
