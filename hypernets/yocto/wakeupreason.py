from hypernets.yocto.init import get_url_base
from urllib.request import urlopen


if __name__ == '__main__':
    url_base = "/".join([get_url_base(), "api", "wakeUpMonitor", "wakeUpReason"])
    str_wakeupreason = urlopen(url_base).read().decode()
       
    print(str_wakeupreason)
