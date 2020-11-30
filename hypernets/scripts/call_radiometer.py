# from shutil import move

from datetime import datetime
from struct import unpack

from hypernets.binary.libhypstar import Hypstar, radiometer, entrance
from hypernets.binary.libhypstar import s_img_data

from argparse import ArgumentParser


def set_tec(TEC=0):
    try:
        hs = Hypstar("/dev/ttyUSB5")
        hs.setTECSetpoint(TEC)

    except Exception as e:
        print(f"Error : {e}")
        return e


def take_picture(path_to_picture=None, params=None):
    # Note : 'params = None' for now, only 5MP is working

    if path_to_picture is None:
        from os import path
        path_to_picture = datetime.utcnow().strftime("%Y%m%dT%H%M%S.jpg")
        path_to_picture = path.join("DATA", path_to_picture)

    try:
        hs = Hypstar("/dev/ttyUSB5")
        im_data = s_img_data()
        hs.acquireDefaultJpeg(True, False, im_data)
        stream = im_data.jpeg_to_bytes()
        with open(path_to_picture, 'wb') as f:
            f.write(stream)
        print(f"Saved to {path_to_picture}.")
        return True

    except Exception as e:
        print(f"Error : {e}")
        return e


def take_spectra(path_to_file, mode, action, it_vnir, it_swir, cap_count):

    rad = {'vis': radiometer.VNIR, 'swi': radiometer.SWIR,
           'bot': radiometer.BOTH}[mode]

    ent = {'rad': entrance.RADIANCE, 'irr': entrance.IRRADIANCE,
           'bla': entrance.DARK}[action]

    print(f"--> [{rad} {ent} {it_vnir} {it_swir}] x {cap_count}")

    try:
        hs = Hypstar('/dev/ttyUSB5')

    except Exception as e:
        print(f"Error : {e}")
        return e

    try:
        cap_list = hs.acquireSpectra(rad, ent, it_vnir, it_swir, cap_count, 0)

        if len(cap_list) == 0:
            return Exception("Cap list length is zero")

        # Concatenation
        spectra = b''
        for n, spectrum in enumerate(cap_list):
            spectra += spectrum.getRawData()
            print(f"Spectrum #{n} added")

        # Save
        with open(path_to_file, "wb") as f:
            f.write(spectra)

        print(f"Saved to {path_to_file}.")

    except Exception as e:
        print(f"Error : {e}")
        return e

    # Read AIT Time from first spectrum in data
    if it_vnir == 0 and mode == "vis":
        it_vnir, = unpack('<H', spectra[11:13])

    if it_swir == 0 and mode == "swi":
        it_swir, = unpack('<H', spectra[11:13])

    if action != "bla" and mode == "bot" and it_swir == 0 and it_vnir == 0:
        print("Warning : do not try dark just after double zero IT")
        print("(not implemented)")
        first_it, = unpack('<H', spectra[11:13])
        it_swir = first_it
        it_vnir = first_it

    return it_vnir, it_swir


if __name__ == '__main__':
    parser = ArgumentParser()

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument("-r", "--rad", action="store_true",
                      help="display relay's states")

    mode.add_argument("-s", "--swir", type=str,
                      help="set the state of the relay",
                      metavar="{on, off}",
                      choices=["on", "off"])

    mode.add_argument("-r", "--both", action="store_true",
                      help="reset relay (1 sec off, then on)")

#    mode.add_argument("-p", "--set-at-power-on", type=str,
#                      help="schedule the state of the relay for next wakeup "
#                           "(use --force [-f] to write in flash memory)",
#                      metavar="{on, off, unchanged}",
#                      choices=["on", "off", "unchanged"])

#    parser.add_argument("-n", "--id-relay", type=int,
#                        help="ID number of the relay (-1 stands for 'all')",
#                        required=True,
#                        metavar="{-1,1..6}",
#                        choices=[-1] + list(range(1, 7, 1)))

#    parser.add_argument("-f", "--force", action="store_true",
#                        help="force relay #1 to switch off")

#    args = parser.parse_args()

#    if args.get:
#        get_state_relay(args.id_relay)

#    elif args.set:
#        set_state_relay(args.id_relay, args.set)

#    elif args.reset:
#        set_state_relay(args.id_relay, "reset")

#    elif args.set_at_power_on:
#        set_at_power_on(args.id_relay, args.set_at_power_on)
#        take_picture()
