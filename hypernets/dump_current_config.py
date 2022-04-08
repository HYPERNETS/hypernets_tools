
from pickle import dump
from hypernets.hypstar.handler import HypstarHandler
from hypernets.yocto.gps import get_gps
from hypernets.yocto.relay import set_state_relay

from logging import info
from argparse import ArgumentParser


def dump_config(hypstar=True, yocto=True, output_file="config.dump"):

    print(hypstar, yocto, output_file)

    if yocto:
        set_state_relay([2], "on")

    if hypstar:

        instrument = HypstarHandler()

        coef_cal = instrument.get_calibration_coeficients_basic()
        serials = instrument.get_serials()

        info(coef_cal)
        info(serials)

        del instrument

    else:
        coef_cal = None
        serials = None

    if yocto:
        set_state_relay([2], "off")
        gps = get_gps()
    else:
        gps = None

    with open(output_file, "wb") as fd:
        dump([serials, coef_cal, gps], fd)


if __name__ == "__main__":

    dt_fmt = '%Y-%m-%dT%H:%M:%S'
    parser = ArgumentParser()

    parser.add_argument("-H", "--hypstar", action='store_true',
                        help="Dump Hypstar Config", default=False)

    parser.add_argument("-y", "--yocto", action='store_true',
                        help="Dump yocto Config", default=False)

    parser.add_argument("-o", "--output", type=str, required=False,
                        help="Specify output file", default="config.dump")

    args = parser.parse_args()

    dump_config(hypstar=args.hypstar, yocto=args.yocto,
                output_file=args.output)
