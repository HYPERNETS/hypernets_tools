from argparse import ArgumentParser
from configparser import ConfigParser
from logging import debug, error
from urllib.request import urlopen
from urllib.error import HTTPError

from hypernets.yocto.init import get_url_base, get_yocto_upper_board_serial

def getPoweroffCountdown():
    try:
        url_base = "/".join([get_url_base(), "api", "wakeUpMonitor", "sleepCountdown"])
        url = urlopen(url_base)
        countdown = int(url.read())
        if countdown == 0:
            debug(f"Yocto auto-power-off is disabled")
        else:
            debug(f"Yocto auto-power-off in {countdown} seconds")

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_upper_board_serial()}' is not online")
        else:           
            error(f"HTTP Error: {e.code}")
        return None

    except Exception as e:
        error(f"{e}")
        return None

    return countdown


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("-f", "--force", action="store_true",
                        help="forces sleep if no wakeup is scheduled")

    args = parser.parse_args()

    try:
        config_dynamic = ConfigParser()
        config_dynamic.read("config_dynamic.ini")
    
        if config_dynamic["general"]["keep_pc"] == "off":
    
            # check if wakeup is scheduled
            url_base = "/".join([get_url_base(), "api", "wakeUpMonitor", "nextWakeUp"])
            url = urlopen(url_base)
            next_wakeup = int(url.read())
    
            # Yocto scheduled wakeup is disabled, exit with code 255
            if next_wakeup == 0 and not args.force:
                exit(255)
    
            else:
                # set sleep countdown timer to 10 s
                get = "?sleepCountdown=10&."
                # print(url_base + get)
                url = urlopen(url_base + get)
                # print(url.code)

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_upper_board_serial()}' is not online")
        else:
            error(f"HTTP Error: {e.code}")
        exit(1)

    except Exception as e:
        error(f"{e}")
        exit(1)


