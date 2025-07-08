from hypernets.yocto.init import get_url_base, get_yocto_upper_board_serial
from urllib.request import urlopen
from urllib.error import HTTPError
from logging import error


if __name__ == '__main__':
    try:
        url_base = "/".join([get_url_base(), "api", "wakeUpMonitor", "wakeUpReason"])
        str_wakeupreason = urlopen(url_base).read().decode()
           
        print(str_wakeupreason)

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_upper_board_serial()}' is not online")
        else:           
            error(f"HTTP Error: {e.code}")

    except Exception as e:
        error(f"{e}")

