# from shutil import move

from datetime import datetime
from struct import unpack

from hypernets.binary.libhypstar import Hypstar, radiometer, entrance
from hypernets.binary.libhypstar import s_img_data

from argparse import ArgumentParser


def set_tec(TEC=5):
    try:
        if TEC == -100:
            print("Disabling Cooling...")
        else:
            print(f"Setting TEC to {TEC} °C...")
        hs = Hypstar("/dev/ttyUSB5")
        hs.setTECSetpoint(TEC)
        print('DONE')

    except Exception as e:
        print(f"Error : {e}")
        return e


def unset_tec():
    set_tec(-100)


def make_datetime_name(extension=".jpg"):
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S")+extension


def take_picture(path_to_file=None, params=None, return_stream=False):

    # Note : 'params = None' for now, only 5MP is working

    if path_to_file is None:
        from os import path
        path_to_file = make_datetime_name()
        path_to_file = path.join("DATA", path_to_file)

    try:
        hs = Hypstar("/dev/ttyUSB5")
        im_data = s_img_data()
        hs.acquireDefaultJpeg(True, False, im_data)
        stream = im_data.jpeg_to_bytes()
        with open(path_to_file, 'wb') as f:
            f.write(stream)
        print(f"Saved to {path_to_file}.")
        if return_stream:
            return stream
        return True

    except Exception as e:
        print(f"Error : {e}")
        return e


def take_spectra(path_to_file, mode, action, it_vnir, it_swir, cap_count):

    rad = {'vis': radiometer.VNIR, 'swi': radiometer.SWIR,
           'bot': radiometer.BOTH}[mode]

    ent = {'rad': entrance.RADIANCE, 'irr': entrance.IRRADIANCE,
           'bla': entrance.DARK}[action]

    if rad in [radiometer.SWIR, radiometer.BOTH]:
        set_tec()

    print(f"--> [{rad} {ent} {it_vnir} {it_swir}] x {cap_count}")

    if path_to_file is None:
        from os import path
        path_to_file = make_datetime_name(extension=".spe")
        path_to_file = path.join("DATA", path_to_file)

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


# FIXME : write more generic function (refactor with take_spectra)
def _cli_extra_parser(args):
    if args.picture:
        take_picture(path_to_file=args.output)

    else:
        if args.radiometer == 'vnir':
            mode = "vis"
        elif args.radiometer == 'swir':
            mode = "swi"
        elif args.radiometer == 'both':
            mode = "bot"

        if args.entrance == 'dark':
            action = 'bla'
        else:
            action = args.entrance

        take_spectra(args.output, mode, action,
                     args.it_vnir, args.it_swir, args.count)


if __name__ == '__main__':

    parser = ArgumentParser()

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument("-p", "--picture", action="store_true",
                      help="Take a picture (5MP)")

    mode.add_argument("-r", "--radiometer", type=str,
                      metavar="{vnir, swir, both}",
                      choices=["vnir", "swir", "both"],
                      help="Select a radiometer")

    parser.add_argument("-e", "--entrance", type=str,
                        metavar="{irr, rad, dark}",
                        choices=["irr", "rad", "dark"],
                        help="Select an entrance")

    parser.add_argument("-v", "--it-vnir", type=int, default=0,
                        help="Integration Time for VNIR (default=0)")

    parser.add_argument("-w", "--it-swir", type=int, default=0,
                        help="Integration Time for SWIR (default=0)")

    parser.add_argument("-n", "--count", type=int, default=1,
                        help="Number of capture (default=1)")

    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Specify output file name")

    args = parser.parse_args()

    if args.radiometer and not args.entrance:
        parser.error(f"Please select an entrance for the {args.radiometer}.")

    if args.entrance and not args.radiometer:
        parser.error(f"Please select a radiometer for {args.entrance}.")

    _cli_extra_parser(args)
