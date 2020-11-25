from hypernets.scripts.spa.spa_py import spa_calc
from configparser import ConfigParser
from datetime import datetime


def spa_from_datetime():

    config = ConfigParser()
    config.read("config_hypernets.ini")

    elevation = float(config["SPA"]["elevation"])
    time_zone = int(config["SPA"]["time_zone"])
    latitude = float(config["GPS"]["latitude"])
    longitude = float(config["GPS"]["longitude"])
    now = datetime.now()

    # TODO : make a choice with alternative :
    # time_zone = 0
    # now = datetime.utcnow()

    spa = spa_calc(year=now.year, month=now.month, day=now.day,
                   hour=now.hour, minute=now.minute, second=now.second,
                   time_zone=time_zone,
                   longitude=longitude,
                   latitude=latitude,
                   elevation=elevation,
                   pressure=820,
                   temperature=11,
                   delta_t=67)

    return spa['azimuth'], spa['zenith']


def spa_from_gps():
    pass


if __name__ == '__main__':
    azimuth_sun, zenith_sun = spa_from_datetime()
    print(f"Azimuth Sun  : {azimuth_sun} ; Zenith Sun : {zenith_sun}")
