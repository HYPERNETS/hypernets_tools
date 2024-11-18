from pysolar.solar import get_altitude, get_azimuth
from datetime import datetime, timezone
import warnings

from logging import info, debug, error


def spa_from_datetime(now=None):

    if now is None:
        now = datetime.now(timezone.utc)

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

    with warnings.catch_warnings(): # ignore pysolar leap seconds warning
        warnings.simplefilter("ignore")

        # use pysolar default values for temperature and pressure
        azimuth = get_azimuth(latitude, longitude, now, elevation)
        zenith = 90 - get_altitude(latitude, longitude, now, elevation)

    info(f"Sun Position  (azimuth : {azimuth:.2f}, "
         f"zenith : {zenith:.2f})")

    return azimuth, zenith


def spa_from_gps():
    from hypernets.yocto.gps import get_gps
    latitude, longitude, now = get_gps()

    if (now == b'N/A'):
        raise Exception("No GPS fix")

    now = datetime.strptime(now, '%Y/%m/%d %H:%M:%S')
    now.replace(tzinfo=timezone.utc) # GPS = utc

    with warnings.catch_warnings(): # ignore pysolar leap seconds warning
        warnings.simplefilter("ignore")

        # use pysolar default values for temperature and pressure
        # TODO test with gps elevation
        azimuth = get_azimuth(latitude, longitude, now, elevation=0)
        zenith = 90 - get_altitude(latitude, longitude, now, elevation=0)

    return azimuth, zenith


if __name__ == '__main__':
    print("From datetime + fixed coords in config_dynamic.ini : ")
    azimuth_sun, zenith_sun = spa_from_datetime()
    print(f"Azimuth Sun  : {azimuth_sun:.3f} ; Zenith Sun : {zenith_sun:.3f}")

    try:
        print("From GPS")
        azimuth_sun, zenith_sun = spa_from_gps()
        print(f"Azimuth Sun  : {azimuth_sun:.3f} ; Zenith Sun : {zenith_sun:.3f}")
    except Exception as e:
        error(f"{e}")

