from hypernets.yocto.init import get_url_base


if __name__ == '__main__':
    from urllib.request import urlopen
    from urllib.error import HTTPError
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

