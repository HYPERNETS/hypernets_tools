"""
05/10/2020 : open_sequence : to read sequence from csv file
"""

from argparse import ArgumentParser

from csv import reader
from time import sleep  # noqa
from datetime import datetime
from os import mkdir, replace, path

import sys
from hypernets.virtual.read_protocol import create_seq_name, create_spectra_name, create_block_position_name
from hypernets.scripts.call_radiometer import take_picture, take_spectra, set_tec, unset_tec
from hypernets.scripts.libhypstar.python.hypstar_wrapper import Hypstar, HypstarLogLevel, wait_for_instrument
from hypernets.scripts.libhypstar.python.data_structs.hardware_info import HypstarSupportedBaudRates
from hypernets.scripts.libhypstar.python.data_structs.environment_log import EnvironmentLogEntry, get_csv_header

last_it_vnir = 0
last_it_swir = 0


def hypstar_python(instrument_instance, line, block_position, output_dir="DATA"):

    global last_it_vnir, last_it_swir

    _, _, _, mode, action, it_vnir, cap_count, total_time = line

    print(f"--> [Mode : {mode} | Action : {action} | IT {it_vnir} ms] x "
          f"{cap_count} | total time : {total_time} ms]")

    if action in ['cal', 'non']:
        output_name = 'NA_' + block_position

    elif action == 'pic':
        if take_picture(instrument_instance, path.join(output_dir, block_position + ".jpg")):
            output_name = block_position + ".jpg"
        else:
            output_name = "ERR_" + block_position + ".jpg"
    else:
        # Tset = 10
        it_swir = it_vnir  # For now

        # TODO : restriction
        it_vnir = int(it_vnir)
        it_swir = int(it_swir)
        cap_count = int(cap_count)

        # TODO Refactor
        if action == 'bla':
            it_vnir = last_it_vnir
            it_swir = last_it_swir

        output_name = block_position + create_spectra_name(line) + ".spe"

        # FIXME : replace by error code..
        try:
            it_vnir, it_swir =\
                take_spectra(instrument_instance, path.join(output_dir, output_name),
                             mode, action, it_vnir, it_swir, cap_count)

            # Update global vars for IT saving
            if mode == 'vis' or mode == 'bot':
                last_it_vnir = it_vnir
                print(f"Last AIT-VNIR is now : {last_it_vnir}")

            if mode == 'swi' or mode == 'bot':
                last_it_swir = it_swir
                print(f"Last AIT-SWIR is now : {last_it_swir}")

        except Exception as e:
            print(f"Error : {e}")
            output_name = "ERR_" + output_name

    return output_name


def check_if_swir_or_park_requested(sequence_file):
    # skip header
    sequence_file.readline()
    swir_strings = ['swi', 'bot']
    park = False
    for line in sequence_file:
        for s in swir_strings:
            if s in line:
                return True, False
        park = park | (line.split(',')[4] == 'non')
    return False, park


def run_sequence_file(sequence_file, instrument_port, instrument_br, instrument_loglevel, driver=True, instrument_standalone=False): # FIXME : # noqa C901
    with open(sequence_file, mode='r') as sequence:

        DATA_DIR = "DATA"  # XXX Add option

        # start = datetime.now()
        start = datetime.utcnow()

        # we should check if any of the lines want to use SWIR and enable TEC
        swir, park = check_if_swir_or_park_requested(sequence)
        print("SWIR:{}, park:{}".format(swir, park))
        # unwind file for processing
        sequence.seek(0)

        # nothing of this is needed for parking sequence
        if not park:
            instrument_instance = None
            # sometimes relay is not actually off, should test for that
            try:
                instrument_instance = Hypstar(instrument_port)
            except IOError as e:
                # wait for instrument to boot on given port. 30s taken from the run_service.sh
                boot_timeout = 15
                if not wait_for_instrument(instrument_port, boot_timeout):
                    # just in case instrument sent BOOTED packet while we were switching baudrates, let's test if it's there
                    try:
                        instrument_instance = Hypstar(instrument_port)
                    except IOError as e:
                        print("[ERROR] Did not get instrument BOOTED packet in {}s".format(boot_timeout))
                        sys.exit(27)

            # initialize instrument once
            try:
                if not instrument_instance:
                    instrument_instance = Hypstar(instrument_port)
                instrument_instance.set_log_level(instrument_loglevel)
                instrument_instance.set_baud_rate(HypstarSupportedBaudRates(instrument_br))
                instrument_instance.get_hw_info()
                # due to the bug in PSU HW revision 3 12V regulator might not start up properly and optical multiplexer is not available
                # since this prevents any spectra acquisition, instrument is unusable and there's no point in continuing
                # instrument power cycling is the only workaround and that's done in run_sequence bash script so we signal it that it's all bad
                if not instrument_instance.hw_info.optical_multiplexer_available:
                    print("[ERROR] MUX+SWIR+TEC hardware not available")
                    sys.exit(27)  # SIGABORT

            except Exception as e:
                print(e)
                # if instrument does not respond, there's no point in doing anything, so we exit with ABORTED signal so that shell script can catch exception
                sys.exit(6)  # SIGABRT

        seq_name = create_seq_name(now=start, prefix="CUR")
        mkdir(path.join(DATA_DIR, seq_name))
        mkdir(path.join(DATA_DIR, seq_name, "RADIOMETER"))

        # XXX Add option :
        # copy(sequence_file, path.join(seq_name, sequence_file))
        # mkdir(path.join(DATA_DIR, seq_name, "WEBCAM"))

        # Write one line meteo file
        # mkdir(path.join(DATA_DIR, seq_name, "METEO"))
        if not instrument_standalone:
            from hypernets.scripts.yocto_meteo import get_meteo
            from hypernets.scripts.pan_tilt import move_to
            from hypernets.scripts.spa.spa_hypernets import spa_from_datetime, spa_from_gps
            with open(path.join(DATA_DIR, seq_name, "meteo.csv"), "w") as meteo:
                try:
                    meteo_data = get_meteo()
                    meteo_data = "; ".join([str(val) + unit for val, unit in meteo_data])  # noqa
                    meteo.write(f"{meteo_data}\n")

                except Exception as e:
                    meteo_data.write(e)

        print(get_csv_header(), flush=True)
        mdfile = open(path.join(DATA_DIR, seq_name, "metadata.txt"), "w")

        if not park:
            # Enabling SWIR TEC for the whole sequence is a tradeoff between current consumption and execution time
            # Although it would seem that disabling TEC while rotating saves power,
            # one has to remember, that during initial thermal regulation TEC consumes 5x more current + does it for longer.
            if swir:
                set_tec(instrument_instance)

        sequence_reader = reader(sequence)

        next(sequence_reader)  # skip header
        for i, line in enumerate(sequence_reader, start=1):
            print(f"== [Line {i}] " + 60*"=")
            # strip leading and trailing spaces
            line = [a.strip() for a in line]
            pan, ref, tilt, _, _, _, _, _ = line
            block_position = create_block_position_name(i, line)
            mdfile.write(f"\n[{block_position}]\n")

            # ---------------------PANTILT SECTION----------------------------
            try:
                pan, tilt = float(pan), float(tilt)

            except Exception as e:  # TODO : catch non float error here
                print(e)            # or check before (seq-checker-script)

            print(f"--> Requested Position (azimuth : {pan:.2f} / {ref} ; "
                  f"zenith : {tilt:.2f})")
            mdfile.write(f"pt_ask={pan:.2f}; {tilt:.2f}\n")

            if not instrument_standalone:
                if ref == "sun":
                    try:
                        azimuth_sun, zenith_sun = spa_from_gps()
                    except Exception as e:
                        print(f"Error : {e}")
                        azimuth_sun, zenith_sun = spa_from_datetime()

                    print(f"--> Sun Position  (azimuth : {azimuth_sun:.2f}, "
                          f"zenith : {zenith_sun:.2f})")

                    if pan == -1 and tilt == -1:
                        print("--> Special position : point to the sun")
                        pan = azimuth_sun
                        tilt = 180 - zenith_sun

                    else:
                        if azimuth_sun <= 180:
                            print(" -- Morning : +90 (=clockwise)")
                            pan = azimuth_sun + pan  # clockwise
                        else:
                            print(" -- Afternoon : -90 (=counter-clockwise)")
                            pan = azimuth_sun - pan  # clockwise

                    print(f"--> Converted Position (pan : {pan:.2f} / {ref} ; "
                          f"tilt :{tilt:.2f})")

                mdfile.write(f"pt_abs={pan:.2f}; {tilt:.2f}\n")

                try:
                    pan_real, tilt_real = move_to(None, pan, tilt, verbose=False,
                                                  wait=True)

                    pan_real = float(pan_real) / 100
                    tilt_real = float(tilt_real) / 100

                except TypeError:
                    pan_real, tilt_real = -999, -999
                    print(f"--> final pan : {pan_real} ; final tilt : {tilt_real}")
                    mdfile.write(f"pt_ref={pan_real:.2f}; {tilt_real:.2f}\n")

                    # ---------------------------------------------------------
                    # if args.phystar:
                    #     output_name = send_to_phystar(line, block_position)
                    #
                    # elif hypstar:
                    #     output_name = send_to_hypstar(line, block_position)
                    # ---------------------------------------------------------
            if not park:
                output_name = hypstar_python(instrument_instance, line, block_position, output_dir=path.
                                             join(DATA_DIR, seq_name, "RADIOMETER"))  # noqa

                now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
                mdfile.write(f"{output_name}={now_str}\n")

        mdfile.close()

        replace(path.join(DATA_DIR, seq_name),
                path.join(DATA_DIR, create_seq_name(now=start)))

        if swir:
            unset_tec(instrument_instance)


if __name__ == '__main__':

    parser = ArgumentParser()

    driver = parser.add_mutually_exclusive_group(required=True)

    driver.add_argument("-d", "--hypstar-dynamic", action='store_true',
                        help="Use dynamic libhypstar driver")

    parser.add_argument("-f", "--file", type=str,
                        help="Select input sequence file",
                        required=True)

    parser.add_argument("--noyocto", action="store_true",
                        help="Run using instrument alone, no meteo or yocto stuff")

    parser.add_argument("-p", "--port", type=str,
                        help="Serial port used for communications with instrument",
                        default="/dev/radiometer0")

    parser.add_argument("-l", "--loglevel", type=str,
                        help="Verbosity of the instrument driver log",
                        choices=[HypstarLogLevel.ERROR.name, HypstarLogLevel.INFO.name, HypstarLogLevel.DEBUG.name, HypstarLogLevel.TRACE.name],
                        default="ERROR")

    parser.add_argument("-b", "--baudrate", type=int,
                        help="Serial port baud rate used for communications with instrument",
                        default=115200)
    # driver.add_argument("-y", "--hypstar", action='store_true',
    #                     help="Use libhypstar driver")

    # driver.add_argument("-p", "--phystar", action='store_true',
    #                     help="Use phystar driver")

    args = parser.parse_args()

    # run_sequence_file(args.file, hypstar=args.hypstar)
    run_sequence_file(args.file, driver=None, instrument_standalone=args.noyocto, instrument_port=args.port, instrument_br=args.baudrate, instrument_loglevel=HypstarLogLevel[args.loglevel.upper()])
