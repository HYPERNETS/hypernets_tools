
from argparse import ArgumentParser

from time import sleep  # noqa
from datetime import datetime
from os import mkdir, replace, path

from hypernets.abstract.protocol import Protocol
from hypernets.abstract.read_protocol import create_seq_name
from hypernets.abstract.create_metadata import parse_config_metadata
from hypernets.abstract.request import EntranceExt, RadiometerExt

from hypernets.scripts.hypstar_handler import HypstarHandler
from hypernets.scripts.libhypstar.python.hypstar_wrapper import HypstarLogLevel



def run_sequence_file(sequence_file, instrument_port, instrument_br, # noqa C901
        instrument_loglevel, instrument_standalone=False,
        DATA_DIR="DATA"): # FIXME : # noqa C901

    protocol = Protocol(sequence_file)
    print(protocol)

    # we should check if any of the lines want to use SWIR and enable TEC :
    swir_is_requested = protocol.check_if_swir_requested()

    if not path.exists(DATA_DIR):  # TODO move management of output folder
        mkdir(DATA_DIR)

    start = datetime.utcnow()  # start = datetime.now()
    seq_name = create_seq_name(now=start, prefix="CUR")
    mkdir(path.join(DATA_DIR, seq_name))
    mkdir(path.join(DATA_DIR, seq_name, "RADIOMETER"))

    # XXX Add option to copy the sequence file ?:
    # copy(sequence_file, path.join(DATA_DIR, seq_name, sequence_file))

    # from hypernets.scripts.pan_tilt import move_to # RM
    from hypernets.scripts.pan_tilt import move_to_geometry  # RM

    if not instrument_standalone:
        from hypernets.scripts.yocto_meteo import get_meteo # noqa
        from hypernets.scripts.pan_tilt import move_to # noqa
        from hypernets.scripts.spa.spa_hypernets import spa_from_datetime, spa_from_gps # noqa

        # mkdir(path.join(DATA_DIR, seq_name, "METEO"))

        # Write one line meteo file
        with open(path.join(DATA_DIR, seq_name, "meteo.csv"), "w") as meteo: # noqa
            try:
                meteo_data = get_meteo()
                meteo_data = "; ".join([str(val) + unit for val, unit in meteo_data])  # noqa
                meteo.write(f"{meteo_data}\n")

            except Exception as e:
                meteo_data.write(e)

    if instrument_standalone:
        instrument_instance = HypstarHandler(instrument_loglevel=instrument_loglevel,  # noqa
                                             instrument_baudrate=instrument_br,
                                             instrument_port=instrument_port,
                                             except_boot_packet=False)

    else:
        instrument_instance = HypstarHandler(instrument_loglevel=instrument_loglevel,  # noqa
                                             instrument_baudrate=instrument_br,
                                             instrument_port=instrument_port,
                                             except_boot_packet=True)
    # Useless ?
    # instrument, visible, swir = instrument_instance.get_serials()
    # print(f"SN : * instrument -> {instrument}")
    # print(f"     * visible    -> {visible}")
    # if swir != 0:
    #     print(f"     * swir       -> {swir}")
    # print(get_csv_header(), flush=True)

    mdfile = open(path.join(DATA_DIR, seq_name, "metadata.txt"), "w")
    mdfile.write(parse_config_metadata())

    # Enabling SWIR TEC for the whole sequence is a tradeoff between
    # current consumption and execution time
    # Although it would seem that disabling TEC while rotating saves
    # power, one has to remember, that during initial thermal regulation
    # TEC consumes 5x more current + does it for longer.
    if swir_is_requested:
        # Does the TEC point should be picked from the config instead of
        # hardcoded ?
        instrument_instance.set_SWIR_module_temperature(0)

    iter_line, nb_error = 0, 0
    for i, (geometry, requests) in enumerate(protocol, start=1):
        print(f"== [Line {i}] " + 60*"=")
        if not instrument_standalone:
            print(f"--> Requested Position : {geometry}")
            try:
                pan_real, tilt_real = move_to_geometry(geometry, wait=True,
                                                       verbose=True)
                pan_real = float(pan_real) / 100
                tilt_real = float(tilt_real) / 100
                print(f"--> final pan : {pan_real} ; final tilt : {tilt_real}")

            except TypeError:
                pan_real, tilt_real = -999, -999

        for request in requests:
            iter_line += 1
            block_position = geometry.create_block_position_name(iter_line)
            now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

            if request.entrance == EntranceExt.PICTURE:
                filename = block_position + ".jpg"
                filepath = path.join(DATA_DIR, seq_name, "RADIOMETER", filename)  # noqa

                try:
                    instrument_instance.take_picture(path_to_file=filepath)
                except Exception as e:
                    print(f"Error : {e}")
                    nb_error += 1
                    filename = "ERR_" + filename

            elif request.radiometer != RadiometerExt.NONE:
                filename = block_position
                filename += request.spectra_name_convention() + ".spe"
                filepath = path.join(DATA_DIR, seq_name, "RADIOMETER", filename)  # noqa

                try:
                    instrument_instance.take_spectra(request, path_to_file=filepath)  # noqa
                except Exception as e:
                    print(f"Error : {e}")
                    nb_error += 1
                    filename = "ERR_" + filename

            mdfile.write(f"\n[{block_position}]\n")
            mdfile.write(f"{filename}={now_str}\n")

            # Write p/t values each blocks for backward compatibility
            mdfile.write(f"pt_ask={geometry.pan:.2f}; {geometry.tilt:.2f}\n")
            # mdfile.write(f"pt_abs={pan:.2f}; {tilt:.2f}\n")
            mdfile.write(f"pt_ref={pan_real:.2f}; {tilt_real:.2f}\n")

    mdfile.close()

    replace(path.join(DATA_DIR, seq_name),
            path.join(DATA_DIR, create_seq_name(now=start)))

    if swir_is_requested is True:
        instrument_instance.shutdown_SWIR_module_thermal_control()


#        if not instrument_standalone:
#            if ref == "sun":
#                try:
#                azimuth_sun, zenith_sun = spa_from_gps()
#                    except Exception as e:
#                        print(f"Error : {e}")
#                        azimuth_sun, zenith_sun = spa_from_datetime()
#
#                    print(f"--> Sun Position  (azimuth : {azimuth_sun:.2f}, "
#                          f"zenith : {zenith_sun:.2f})")
#
#                    if pan == -1 and tilt == -1:
#                        print("--> Special position : point to the sun")
#                        pan = azimuth_sun
#                        tilt = 180 - zenith_sun
#
#                    else:
#                        if azimuth_sun <= 180:
#                            print(" -- Morning : +90 (=clockwise)")
#                            pan = azimuth_sun + pan  # clockwise
#                        else:
#                            print(" -- Afternoon : -90 (=counter-clockwise)")
#                            pan = azimuth_sun - pan  # clockwise
#
#                    print(f"--> Converted Position (pan : {pan:.2f} / {ref} ;"
#                          f"tilt :{tilt:.2f})")
#
#                mdfile.write(f"pt_abs={pan:.2f}; {tilt:.2f}\n")
#
#                try:
#                    pan_real, tilt_real = move_to(None, pan, tilt, wait=True,
#                                                  verbose=False)
#
#                    pan_real = float(pan_real) / 100
#                    tilt_real = float(tilt_real) / 100
#
#                except TypeError:
#                    pan_real, tilt_real = -999, -999
#                    print(f"--> final pan : {pan_real} ; final tilt : {tilt_real}") #noqa
#                    mdfile.write(f"pt_ref={pan_real:.2f}; {tilt_real:.2f}\n")


if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument("-f", "--file", type=str,
                        help="Select input sequence file",
                        required=True)

    parser.add_argument("--noyocto", action="store_true",
                        help="Run using instrument alone, no meteo or yocto stuff") #noqa

    parser.add_argument("-p", "--port", type=str,
                        help="Serial port used for communications with instrument", #noqa
                        default="/dev/radiometer0")

    parser.add_argument("-l", "--loglevel", type=str,
                        help="Verbosity of the instrument driver log",
                        choices=[HypstarLogLevel.ERROR.name,
                                 HypstarLogLevel.INFO.name,
                                 HypstarLogLevel.DEBUG.name,
                                 HypstarLogLevel.TRACE.name], default="ERROR")

    parser.add_argument("-b", "--baudrate", type=int,
                        help="Serial port baud rate used for communications with instrument", # noqa
                        default=3000000)

    args = parser.parse_args()

    print(80*"-" + f"\n{args}\n" + 80*"-")

    run_sequence_file(args.file,
                      instrument_standalone=args.noyocto,
                      instrument_port=args.port, instrument_br=args.baudrate,
                      instrument_loglevel=HypstarLogLevel[args.loglevel.upper()]) # noqa
