"""
05/10/2020 : Mini-pyxis to execute sequence from csv file
"""

from argparse import ArgumentParser

from csv import reader
from time import sleep  # noqa
from datetime import datetime
from os import mkdir, replace, path

from hypernets.virtual.read_protocol import create_seq_name
from hypernets.virtual.read_protocol import create_spectra_name
from hypernets.virtual.read_protocol import create_block_position_name

from hypernets.scripts.pan_tilt import move_to
from hypernets.scripts.spa.spa_hypernets import spa_from_datetime, spa_from_gps
from hypernets.scripts.call_radiometer import take_picture, take_spectra
from hypernets.scripts.call_radiometer import unset_tec
from hypernets.scripts.yocto_meteo import get_meteo


last_it_vnir = 0
last_it_swir = 0
swir = False


def hypstar_python(line, block_position, output_dir="DATA"):

    global last_it_vnir, last_it_swir, swir

    _, _, _, mode, action, it_vnir, cap_count, total_time = line

    print(f"--> [Mode : {mode} | Action : {action} | IT {it_vnir} ms] x "
          f"{cap_count} | total time : {total_time} ms]")

    if action in ['cal', 'non']:
        output_name = 'NA_' + block_position

    elif action == 'pic':
        if take_picture(path.join(output_dir, block_position + ".jpg")):
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
                take_spectra(path.join(output_dir, output_name),
                             mode, action, it_vnir, it_swir, cap_count)

            # Update global vars for IT saving
            if mode == 'vis' or mode == 'bot':
                last_it_vnir = it_vnir
                print(f"Last AIT-VNIR is now : {last_it_vnir}")

            if mode == 'swi' or mode == 'bot':
                swir = True
                last_it_swir = it_swir
                print(f"Last AIT-SWIR is now : {last_it_swir}")

        except Exception as e:
            print(f"Error : {e}")
            output_name = "ERR_" + output_name

    return output_name


def run_sequence_file(sequence_file, driver=True): # FIXME : # noqa C901
    with open(sequence_file, mode='r') as sequence:

        DATA_DIR = "DATA"  # XXX Add option

        # start = datetime.now()
        start = datetime.utcnow()

        seq_name = create_seq_name(now=start, prefix="CUR")
        mkdir(path.join(DATA_DIR, seq_name))
        mkdir(path.join(DATA_DIR, seq_name, "RADIOMETER"))

        # XXX Add option :
        # copy(sequence_file, path.join(seq_name, sequence_file))
        # mkdir(path.join(DATA_DIR, seq_name, "WEBCAM"))

        # Write one line meteo file
        # mkdir(path.join(DATA_DIR, seq_name, "METEO"))
        # with open(path.join(DATA_DIR, seq_name, "METEO", "meteo.csv"), "w") as meteo:  # noqa
        with open(path.join(DATA_DIR, seq_name, "meteo.csv"), "w") as meteo:
            try:
                meteo_data = get_meteo()
                meteo_data = "; ".join([str(val) + unit for val, unit in meteo_data])  # noqa
                meteo.write(meteo_data)

            except Exception as e:
                meteo_data.write(e)

        mdfile = open(path.join(DATA_DIR, seq_name, "metadata.txt"), "w")
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
                    pan += azimuth_sun  # XXX : here '+' means clockwise
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
            output_name = hypstar_python(line, block_position, output_dir=path.
                                         join(DATA_DIR, seq_name, "RADIOMETER"))  # noqa

            # TODO utc ? should be :
            # now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            now_str = datetime.now().strftime("%Y%m%dT%H%M%S")
            mdfile.write(f"{output_name}={now_str}\n")

        mdfile.close()

        replace(path.join(DATA_DIR, seq_name),
                path.join(DATA_DIR, create_seq_name(now=start)))
    if swir:
        unset_tec()


if __name__ == '__main__':

    parser = ArgumentParser()

    driver = parser.add_mutually_exclusive_group(required=True)

    driver.add_argument("-d", "--hypstar-dynamic", action='store_true',
                        help="Use dynamic libhypstar driver")

    parser.add_argument("-f", "--file", type=str,
                        help="Select input sequence file",
                        required=True)

    # driver.add_argument("-y", "--hypstar", action='store_true',
    #                     help="Use libhypstar driver")

    # driver.add_argument("-p", "--phystar", action='store_true',
    #                     help="Use phystar driver")

    args = parser.parse_args()
    # run_sequence_file(args.file, hypstar=args.hypstar)

    run_sequence_file(args.file, driver=None)
