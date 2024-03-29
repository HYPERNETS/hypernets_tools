from hypernets.geometry.spa.spa_py import spa_calc
from datetime import datetime

from logging import info, debug


def spa_from_datetime(now=None):

    if now is None:
        now = datetime.utcnow()

    from configparser import ConfigParser
    config = ConfigParser()
    config.read("config_dynamic.ini")

    try:
        elevation = float(config["SPA"]["elevation"])
    except KeyError:
        elevation = 0.0

    latitude = float(config["GPS"]["latitude"])
    longitude = float(config["GPS"]["longitude"])

    debug(f"Latitude from config : {latitude}")
    debug(f"Longitude from config : {longitude}")

    spa = spa_calc(year=now.year, month=now.month, day=now.day,
                   hour=now.hour, minute=now.minute, second=now.second,
                   time_zone=0,
                   longitude=longitude,
                   latitude=latitude,
                   elevation=elevation,
                   pressure=820,
                   temperature=11,
                   delta_t=67)

    info(f"Sun Position  (azimuth : {spa['azimuth']:.2f}, "
         f"zenith : {spa['zenith']:.2f})")

    return spa['azimuth'], spa['zenith']


def spa_from_gps():
    from hypernets.yocto.gps import get_gps
    latitude, longitude, now = get_gps()
    # TODO : test the gps trame
    now = datetime.strptime(now, '%Y/%m/%d %H:%M:%S')
    spa = spa_calc(year=now.year, month=now.month, day=now.day,
                   hour=now.hour, minute=now.minute, second=now.second,
                   time_zone=0,  # GPS = utc
                   longitude=longitude,
                   latitude=latitude,
                   elevation=0,  # TODO : test with elevation
                   pressure=820,
                   temperature=11,
                   delta_t=67)

    return spa['azimuth'], spa['zenith']


if __name__ == '__main__':
    print("From datetime + fixed coords in config_dynamic.ini : ")
    azimuth_sun, zenith_sun = spa_from_datetime()
    print(f"Azimuth Sun  : {azimuth_sun} ; Zenith Sun : {zenith_sun}")
    print("From GPS")
    azimuth_sun, zenith_sun = spa_from_gps()
    print(f"Azimuth Sun  : {azimuth_sun} ; Zenith Sun : {zenith_sun}")
