from datetime import datetime

from argparse import ArgumentParser

from .libhypstar.python.data_structs.spectrum_raw import RadiometerType,\
    RadiometerEntranceType

from .libhypstar.python.hypstar_wrapper import Hypstar


def get_serials(instrument_instance):
    try:
        print("Getting SN")
        instrument = instrument_instance.hw_info.instrument_serial_number
        visible = instrument_instance.hw_info.vis_serial_number
        swir = instrument_instance.hw_info.swir_serial_number
        return instrument, visible, swir

    except Exception as e:
        print(f"Error : {e}")
        return e


def instanciation():
    # FIXME :GUI mode : quickfix
    from configparser import ConfigParser
    config = ConfigParser()
    config.read("config_static.ini")
    instrument_port = "/dev/radiometer0"

    try:
        instrument_port = config["general"]["hypstar_port"]
    except KeyError as e:
        print(f"Error : {e}")
        print(f"Use default port {instrument_port}")

    instrument_instance = Hypstar(instrument_port)
    return instrument_instance


def get_env_log(instrument_instance):
    if instrument_instance is None:
        instrument_instance = instanciation()
    log = instrument_instance.get_env_log()  # XXX not sure + catch excpt
    return str(log)

def get_hw_info(instrument_instance):
    if instrument_instance is None:
        instrument_instance = instanciation()
    instrument_instance.get_hw_info()  # XXX not sure + catch excpt
    return str(instrument_instance.hw_info)


def set_tec(instrument_instance, TEC=0):
    if instrument_instance is None:
        instrument_instance = instanciation()
    try:
        if TEC == -100:
            print("Disabling Cooling...")
            instrument_instance.shutdown_SWIR_module_thermal_control()
        else:
            print(f"Setting TEC to {TEC} °C...")
            instrument_instance.set_SWIR_module_temperature(TEC)
        print('DONE')

    except Exception as e:
        print(f"Error : {e}")
        return e


def unset_tec(instrument_instance):
    if instrument_instance is None:
        instrument_instance = instanciation()
    set_tec(instrument_instance, -100)


def make_datetime_name(extension=".jpg"):
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S") + extension


def take_picture(instrument_instance, path_to_file=None, params=None,
                 return_stream=False):

    # Note : 'params = None' for now, only 5MP is working

    if path_to_file is None:
        from os import path, mkdir
        path_to_file = make_datetime_name()
        if not path.exists("DATA"):
            mkdir("DATA")
        path_to_file = path.join("DATA", path_to_file)

    if instrument_instance is None:
        instrument_instance = instanciation()

    try:
        packet_count = instrument_instance.capture_JPEG_image(flip=True)
        if not packet_count:
            return False
        stream = instrument_instance.download_JPEG_image()
        with open(path_to_file, 'wb') as f:
            f.write(stream)
        print(f"Saved to {path_to_file}.")
        if return_stream:
            return stream
        return True

    except Exception as e:
        print(f"Error : {e}")
        return e


def take_spectra(instrument_instance, path_to_file, mode, action, it_vnir, it_swir, cap_count, # noqa 901
                 gui=False, return_cap_list=False, set_time=True):

    rad = {'vis': RadiometerType.VIS_NIR, 'swi': RadiometerType.SWIR,
           'bot': RadiometerType.BOTH}[mode]

    ent = {'rad': RadiometerEntranceType.RADIANCE,
           'irr': RadiometerEntranceType.IRRADIANCE,
           'bla': RadiometerEntranceType.DARK}[action]

    print(f"--> [{rad} {ent} {it_vnir} {it_swir}] x {cap_count}")

    if path_to_file is None:
        from os import path, mkdir
        if not path.exists("DATA"):
            mkdir("DATA")
        path_to_file = make_datetime_name(extension=".spe")
        path_to_file = path.join("DATA", path_to_file)

    if instrument_instance is None:
        instrument_instance = instanciation()

    try:
        # get latest environmental log and print it to output log
        env_log = instrument_instance.get_env_log()
        print(env_log.get_csv_line(), flush=True)
        capture_count = instrument_instance.capture_spectra(rad, ent, it_vnir,
                                                            it_swir, cap_count, 0) # noqa
        slot_list = instrument_instance.get_last_capture_spectra_memory_slots(
            capture_count)
        cap_list = instrument_instance.download_spectra(slot_list)

        if len(cap_list) == 0:
            return Exception("Cap list length is zero")

        # XXX : Very alpha version
        if return_cap_list is True:
            return cap_list

        # Concatenation
        spectra = b''
        for n, spectrum in enumerate(cap_list):
            spectrum_data = spectrum.getBytes()
            spectra += spectrum_data
            # Read ITs :
            if it_vnir == 0 and spectrum.spectrum_header.spectrum_config.vnir:
                it_vnir = spectrum.spectrum_header.integration_time_ms
                # print(f"AIT update : {spectrum.radiometer}->{it_vnir} ms")
            # elif it_swir == 0 and spectrum.radiometer == Radiometer.SWIR:
            elif it_swir == 0 and spectrum.spectrum_header.spectrum_config.swir: # noqa
                # it_swir, = unpack('<H', spectrum_data[11:13])
                it_swir = spectrum.spectrum_header.integration_time_ms
                # print(f"AIT update : {spectrum.radiometer}->{it_swir} ms")

        # Save
        with open(path_to_file, "wb") as f:
            f.write(spectra)

        print(f"Saved to {path_to_file}.")

    except Exception as e:
        print(f"Error : {e}")
        return e

    if gui:
        return it_vnir, it_swir, path_to_file

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

        take_spectra(None, args.output, mode, action,
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
