
from argparse import ArgumentParser

from datetime import datetime
from time import time
from os import mkdir, replace, path
from shutil import copy

from hypernets.abstract.protocol import Protocol
from hypernets.abstract.create_metadata import parse_config_metadata

from hypernets.hypstar.handler import HypstarHandler
from hypernets.hypstar.libhypstar.python.hypstar_wrapper import HypstarLogLevel
from hypernets.hypstar.libhypstar.python.data_structs.environment_log import get_csv_header

from logging import debug, info, warning, error # noqa

from hypernets.yocto.lightsensor_logger import start_lightsensor_thread, terminate_lightsensor_thread


def run_sequence_file(sequence_file, instrument_port, instrument_br, # noqa C901
                      instrument_loglvl, instrument_boot_timeout,
                      instrument_standalone=False,
                      instrument_swir_tec=0,
                      dump_environment_logs=False,
                      DATA_DIR="DATA"):

    protocol = Protocol(sequence_file)
    info(protocol)

    # check if this protocol wants to use instrument
    instrument_is_requested = protocol.check_if_instrument_requested()

    # we should check if any of the lines want to use SWIR and enable TEC :
    swir_is_requested = protocol.check_if_swir_requested()

    # just print out info about presence or not of VM request
    protocol.check_if_vm_requested()

    if not path.exists(DATA_DIR):  # TODO move management of output folder
        mkdir(DATA_DIR)

    start_time = time()  # for ellapsed time
    flags_dict = {}

    start = datetime.utcnow()  # start = datetime.now()
    seq_name = Protocol.create_seq_name(now=start, prefix="CUR")

    seq_path = path.join(DATA_DIR, seq_name)
    final_seq_path = path.join(DATA_DIR, Protocol.create_seq_name(now=start))

    suffix = ""

    n = 0
    while path.isdir(seq_path + suffix) or path.isdir(final_seq_path + suffix):
        n += 1
        error(f"Directory [{seq_path+suffix} or "
              f"{final_seq_path+suffix}] already exists!")
        suffix = f"-{n:03d}"

    # XXX Draft!
    seq_path = seq_path + suffix
    seq_name = seq_name + suffix
    filepath = path.join(seq_path, "RADIOMETER")
    final_seq_path = path.join(DATA_DIR, Protocol.create_seq_name(now=start,
                               suffix=suffix))

    info(f"Creating directories: {seq_path} and {filepath}...")

    mkdir(seq_path)
    mkdir(filepath)

    # XXX Add option to copy
    copy(sequence_file, path.join(seq_path, path.basename(sequence_file)))

    if not instrument_standalone:
        from hypernets.geometry.pan_tilt import move_to_geometry
        from hypernets.yocto.meteo import get_meteo
        except_boot = True

        # mkdir(path.join(seq_path, "METEO"))
        # Write one line meteo file
        with open(path.join(DATA_DIR, seq_name, "meteo.csv"), "w") as meteo:
            try:
                meteo_data = get_meteo()
                meteo_data = "; ".join([str(val) + str(unit)
                                        for val, unit in meteo_data])

                meteo.write(f"{meteo_data}\n")

            except Exception as e:
                meteo.write(e)

        # Start monitor photodiode logging in a separate thread
        monitor_pd_path = path.join(DATA_DIR, seq_name, "monitorPD.csv")
        monitor_pd_thread, monitor_pd_event = start_lightsensor_thread(monitor_pd_path)

    else:
        except_boot = False

    if instrument_is_requested:
        instrument_instance = HypstarHandler(instrument_loglevel=instrument_loglvl,  # noqa
                                             instrument_baudrate=instrument_br,
                                             instrument_port=instrument_port,
                                             expect_boot_packet=except_boot,
                                             boot_timeout=instrument_boot_timeout)   # noqa

        instrument_sn, visible_sn, swir_sn, vm_sn = instrument_instance.get_serials()
        debug(f"SN : * instrument -> {instrument_sn}")
        debug(f"     * visible    -> {visible_sn}")
        if swir_sn != 0:
            debug(f"     * swir       -> {swir_sn}")
        if vm_sn != 0:
            debug(f"     * vm         -> {vm_sn}")
            
        (instrument_FW_major, instrument_FW_minor, instrument_FW_rev, 
         vm_FW_major, vm_FW_minor, vm_FW_rev) = instrument_instance.get_firmware_versions()
        debug(f"FW : * instrument -> {instrument_FW_major}.{instrument_FW_minor}.{instrument_FW_rev}")
        if vm_sn != 0:
            debug(f"     * vm         -> {vm_FW_major}.{vm_FW_minor}.{vm_FW_rev}")        

    mdfile = open(path.join(seq_path, "metadata.txt"), "w")
    mdfile.write(parse_config_metadata(instrument_sn = instrument_sn, vm_sn = vm_sn))

    # Enabling SWIR TEC for the whole sequence is a tradeoff between
    # current consumption and execution time.
    # Although it would seem that disabling TEC while rotating saves
    # power, one has to remember, that during initial thermal regulation
    # TEC consumes 5x more current + does it for longer.
    if swir_is_requested:
        info(f"Cooling SWIR module to {instrument_swir_tec}°C...")
        instrument_instance.set_SWIR_module_temperature(instrument_swir_tec)
        info("Done!")

    # print env log header
    if dump_environment_logs:
        info(get_csv_header())

    iter_line, nb_error = 0, 0
    for i, (geometry, requests) in enumerate(protocol, start=1):

        flags_dict["$elapsed_time"] = time() - start_time

        info(f"== [Line {i}] " + 60*"=")
        info(f"--> {len(geometry.flags)} flags for this geometry")
        # TODO : LOG
        # if len(geometry.flags) != 0:
        #     print("    With :")
        #     for key, value in flags_dict.items():
        #         print(f"\t- {key} : {value}")

        flag_condition = True
        for j, flag in enumerate(geometry.flags, start=1):
            try:
                variable, operator, value = protocol.flags[flag]
                info(f"\n {j}) {variable} [{operator.__name__}] {value}")

                try:
                    flag_condition = operator(flags_dict[variable], value)
                    info(f" --> {flags_dict[variable]} [{operator.__name__}]"
                         f" {value} => {flag_condition}")

                except Exception as e:
                    error(f" {j}) Error : {e}")

            except KeyError:
                warning(f" {j}) (ignored) {flag} must be defined first !")

        if not flag_condition:
            info(f" --> Skipping this Geometry because of the flag : {flag}")
            continue

        info("-"*72)
        if not instrument_standalone:
            geometry.get_absolute_pan_tilt()
            info(f"--> Requested Position : {geometry}")
            try:
                pan_real, tilt_real = move_to_geometry(geometry, wait=True)
                pan_real = float(pan_real) / 100
                tilt_real = float(tilt_real) / 100
                info(f"--> final pan : {pan_real} ; final tilt : {tilt_real}")
                info("-"*72)

            except TypeError:
                pan_real, tilt_real = -999, -999

        for request in requests:
            iter_line += 1

            block_position = geometry.create_block_position_name(iter_line)
            now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

            info(f"{iter_line}) {request} : {now_str}")

            filename = request.spectra_name_convention(prefix=block_position)
            output = path.join(filepath, filename)

            try:
                if dump_environment_logs:
                    # 0xFF returns live data, 0 returns last captured on FW > 0.15.24
                    if (instrument_FW_major, instrument_FW_minor, instrument_FW_rev) > (0, 15, 24):
                        env_request = 0xff 
                    else:
                        env_request = 0

                    env = instrument_instance.get_env_log(env_request)
                    info(env.get_csv_line())
                instrument_instance.take_request(request, path_to_file=output)

            except Exception as e:
                error(f"Error : {e}")
                nb_error += 1

            flags_dict[f"$spectra_file{iter_line}.it_vnir"] = request.it_vnir
            flags_dict[f"$spectra_file{iter_line}.it_swir"] = request.it_swir

            mdfile.write(f"\n[{block_position}]\n")
            mdfile.write(f"{filename}={now_str}\n")

            # Write p/t values each blocks for backward compatibility
            mdfile.write(f"pt_ask={geometry.pan:.2f}; {geometry.tilt:.2f}\n")
            mdfile.write(f"pt_abs={geometry.pan_abs:.2f};"
                         f"{geometry.tilt_abs:.2f}\n")

            # FIXME : quickfix when standalone
            if instrument_standalone:
                pan_real, tilt_real = 0.0, 0.0
            mdfile.write(f"pt_ref={pan_real:.2f}; {tilt_real:.2f}\n")

    mdfile.close()

    terminate_lightsensor_thread(monitor_pd_thread, monitor_pd_event)

    replace(seq_path, final_seq_path)
    info(f"Created sequence : {final_seq_path}")

    if swir_is_requested is True:
        instrument_instance.shutdown_SWIR_module_thermal_control()

    if instrument_is_requested:
        del instrument_instance

#        if not instrument_standalone:
#            if azimuth_sun <= 180:
#                print(" -- Morning : +90 (=clockwise)")
#                pan = azimuth_sun + pan  # clockwise
#            else:
#                print(" -- Afternoon : -90 (=counter-clockwise)")
#                pan = azimuth_sun - pan  # clockwise


if __name__ == '__main__':

    from logging import ERROR, WARNING, INFO, DEBUG, basicConfig

    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%Y-%m-%dT%H:%M:%S'

    # from logging import CRITICAL
    # log_levels = {"CRITICAL": CRITICAL, "ERROR": ERROR, "WARNING": WARNING,
    #               "INFO": INFO, "DEBUG": DEBUG}

    log_levels = {"ERROR": ERROR, "WARNING": WARNING, "INFO": INFO,
                  "DEBUG": DEBUG}

    parser = ArgumentParser()

    parser.add_argument("-f", "--file", type=str,
                        help="Select input sequence file",
                        required=True)

    parser.add_argument("-v", "--verbosity", type=str,
                        help="Verbosity of the sequence maker log.",
                        choices=log_levels.keys(), default="INFO")

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

    parser.add_argument("-t", "--timeout", type=int,
                        help="Boot timeout for the instrument",
                        default=30)

    parser.add_argument("-T", "--swir-tec", type=int,
                        help="Thermoelectric Cooler Point for the SWIR module",
                        default=0)

    parser.add_argument("-e", "--log-environment", action='store_true',
                        help="Dumps instrument environmental logs to stdout",
                        default=False)

    args = parser.parse_args()

    basicConfig(level=log_levels[args.verbosity], format=log_fmt, datefmt=dt_fmt) # noqa

    info("\n" + 80*"-" + f"\n{args}\n" + 80*"-")

    run_sequence_file(args.file,
                      instrument_port=args.port, instrument_br=args.baudrate,
                      instrument_loglvl=HypstarLogLevel[args.loglevel.upper()],
                      instrument_boot_timeout=args.timeout,
                      instrument_standalone=args.noyocto,
                      instrument_swir_tec=args.swir_tec,
                      dump_environment_logs=args.log_environment)
