from argparse import ArgumentParser
from hypernets.yocto.init import get_url_base
from urllib.request import urlopen
from urllib.error import HTTPError

def print_brownout():
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


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("-b", "--brownout", action="store_true",
                        help="print brown-out protection status")

    args = parser.parse_args()

    if args.brownout:
        print_brownout()

    else:
        url_base = "/".join([get_url_base(), "api", "dualPower", "extVoltage"])

        try:
            url = urlopen(url_base)
            voltage = int(url.read()) / 1000
            print(voltage)
        except HTTPError as e:
            if e.code == 404:
                # host system V4 or newer
                url_base = "/".join([get_url_base(), "api", "voltage", "currentValue"])
                url = urlopen(url_base)

                voltage_str = url.read()
                voltage = float(voltage_str.decode('utf-8'))
                print(voltage)
            else:
                print(f"HTTP Error: {e.code}")

