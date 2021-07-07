

from pickle import dump
from hypernets.hypstar.hypstar_handler import HypstarHandler
from hypernets.yocto.gps import get_gps
from hypernets.yocto.relay import set_state_relay

if __name__ == "__main__":

    output_file = "config.dump"

    gps = get_gps()
    set_state_relay([2], "on")

    instrument = HypstarHandler()

    coef_cal = instrument.get_calibration_coeficients_basic()
    serials = instrument.get_serials()

    print(coef_cal)
    print(serials)

    del instrument
    set_state_relay([2], "off")

    with open(output_file, "wb") as fd:
        dump([serials, coef_cal, gps], fd)
