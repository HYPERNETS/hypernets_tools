from argparse import ArgumentParser
from hypernets.yocto.init import get_url_base, get_yocto_gen, get_yocto_upper_board_serial
from urllib.request import urlopen
from urllib.error import HTTPError
from logging import error


def print_brownout():
    try:
        ## supported only by 2nd gen Yocto
        if get_yocto_gen() != "2":
            error("Brown-out protection is supported only by Yocto-Pictor-GPS")
            return(-1)

        url_base = "/".join([get_url_base(), "api", "threshold", "thresholdState"])
        url = urlopen(url_base)
        response_str = url.read()
        state = response_str.decode('utf-8')
    
        url_base = "/".join([get_url_base(), "api", "threshold", "alertLevel"])
        url = urlopen(url_base)
        response_str = url.read()
        alert_lvl = float(response_str.decode('utf-8'))
    
        url_base = "/".join([get_url_base(), "api", "threshold", "safeLevel"])
        url = urlopen(url_base)
        response_str = url.read()
        safe_lvl = float(response_str.decode('utf-8'))

        print(f"Brown-out protection trigger/restore limits: {alert_lvl} V / {safe_lvl} V; current state is {state}")
        return(0)

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto module '{get_yocto_upper_board_serial()}' is not online")
        else:
            error(f"HTTP Error: {e.code}")
        return(-1)

    except Exception as e:
        error(f"{e}")
        return(-1)


def get_voltage():
    try:
        yocto_gen = get_yocto_gen()

        if yocto_gen == "1":
            url_base = "/".join([get_url_base(), "api", "dualPower", "extVoltage"])
            url = urlopen(url_base)
            voltage = int(url.read()) / 1000
        elif yocto_gen == "2":
            url_base = "/".join([get_url_base(), "api", "voltage", "currentValue"])
            url = urlopen(url_base)
            voltage_str = url.read()
            voltage = float(voltage_str.decode('utf-8'))

    except HTTPError as e:
        if e.code == 404:
            error(f"Yocto generation {yocto_gen} module '{get_yocto_upper_board_serial()}' is not online")
        else:
            error(f"HTTP Error: {e.code}")
        return None

    except Exception as e:
        error(f"{e}")
        return None

    return voltage


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("-b", "--brownout", action="store_true",
                        help="print brown-out protection status")

    args = parser.parse_args()

    if args.brownout:
        retcode = print_brownout()
    else:
        voltage = get_voltage()
        if voltage is not None:
            print(voltage)
            retcode = 0
        else:
            retcode = -1
    
    exit(retcode)


