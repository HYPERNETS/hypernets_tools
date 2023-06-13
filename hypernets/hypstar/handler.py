
from sys import exit
from time import sleep
from os.path import exists, islink

from argparse import ArgumentParser

from hypernets.abstract.request import Request, EntranceExt, RadiometerExt

from hypernets.hypstar.libhypstar.python.hypstar_wrapper import Hypstar, \
    wait_for_instrument

from hypernets.hypstar.libhypstar.python.hypstar_wrapper import HypstarLogLevel

from hypernets.hypstar.libhypstar.python.data_structs.hardware_info import \
    HypstarSupportedBaudRates

from hypernets.hypstar.libhypstar.python.data_structs.varia import \
        ValidationModuleLightType

from hypernets.hypstar.libhypstar.python.data_structs.spectrum_raw  \
        import RadiometerEntranceType

from logging import debug, info, error


class HypstarHandler(Hypstar):
    def __init__(self, instrument_port="/dev/radiometer0",
                 instrument_baudrate=115200, instrument_loglevel=3,
                 expect_boot_packet=True, boot_timeout=30):

        HypstarHandler.wait_for_instrument_port(instrument_port)

        if expect_boot_packet and not wait_for_instrument(instrument_port, boot_timeout): # noqa
            # just in case instrument sent BOOTED packet while we were
            # switching baudrates, let's test if it's there
            try:
                super().__init__(instrument_port)

            except IOError as e:
                error(f"{e}")
                error("Did not get instrument BOOTED packet in {}s".format(boot_timeout)) # noqa
                exit(27)

            except Exception as e:
                error(f"{e}")

        else:  # Got the boot packet or boot packet is not expected (gui mode)
            try:
                super().__init__(instrument_port)

            except Exception as e:
                error(f"{e}")
                exit(6)

        try:
            self.set_log_level(instrument_loglevel)
            self.set_baud_rate(HypstarSupportedBaudRates(instrument_baudrate))
            self.get_hw_info()
            # due to the bug in PSU HW revision 3 12V regulator might not start
            # up properly and optical multiplexer is not available since this
            # prevents any spectra acquisition, instrument is unusable and
            # there's no point in continuing instrument power cycling is the
            # only workaround and that's done in run_sequence bash script so we
            # signal it that it's all bad
            if not self.hw_info.optical_multiplexer_available:
                error("MUX+SWIR+TEC hardware not available")
                exit(27)  # SIGABORT

        except IOError as e:
            error(f"{e}")
            exit(6)

        except Exception as e:
            error(e)
            # if instrument does not respond, there's no point in doing
            # anything, so we exit with ABORTED signal so that shell script can
            # catch exception
            exit(6)  # SIGABRT

        env_log = self.get_env_log()
        debug(env_log)

    def __del__(self):
        env_log = self.get_env_log()
        debug(env_log)

    @staticmethod
    def wait_for_instrument_port(instrument_port):
        info(f"Waiting for {instrument_port}...")
        timeout = 5
        while not exists(instrument_port):
            sleep(1)
            timeout -= 1
            debug(f"Timeout remaining value: {timeout}s")
            if timeout <= 0:
                raise Exception(f"{instrument_port} timed out!")
                exit(27)

        if not islink(instrument_port):
            raise ValueError(f"{instrument_port} is not a link!")
            exit(27)

    def take_request(self, request, path_to_file=None, gui=False):

        if path_to_file is None:
            from os import path, mkdir
            path_to_file = path.join("DATA", request.spectra_name_convention())

            if not exists("DATA"):
                mkdir("DATA")

        if request.entrance == EntranceExt.PICTURE:
            self.take_picture(path_to_file)

        elif request.entrance == EntranceExt.VM:
            self.take_validation(request, path_to_file)

        elif request.radiometer != RadiometerExt.NONE:
            self.take_spectra(request, path_to_file)

        return path_to_file

    def take_picture(self, path_to_file, params=None, return_stream=False):
        # Note : 'params = None' for now, only 5MP is working
        try:
            self.packet_count = self.capture_JPEG_image(flip=True)
            if not self.packet_count:
                return False
            stream = self.download_JPEG_image()
            with open(path_to_file, 'wb') as f:
                f.write(stream)

            debug(f"Saved to {path_to_file}.")
            if return_stream:
                return stream
            return True

        except Exception as e:
            error(f"{e}")
            return e

    def take_spectra(self, request, path_to_file, overwrite_IT=True):

        try:
            cap_count = self.capture_spectra(request.radiometer,
                                             request.entrance,
                                             request.it_vnir,
                                             request.it_swir,
                                             request.number_cap,
                                             request.total_measurement_time)

            slot_list = self.get_last_capture_spectra_memory_slots(cap_count)
            cap_list = self.download_spectra(slot_list)

            if len(cap_list) == 0:
                return Exception("Cap list length is zero!")

            # Concatenation
            spectra = b''
            for n, spectrum in enumerate(cap_list):
                spectra += spectrum.getBytes()

                debug(spectrum)

                if overwrite_IT:
                    if spectrum.spectrum_header.spectrum_config.vnir:
                        request.it_vnir = \
                            spectrum.spectrum_header.integration_time_ms
                    elif spectrum.spectrum_header.spectrum_config.swir:
                        request.it_swir = \
                            spectrum.spectrum_header.integration_time_ms

            # Save
            with open(path_to_file, "wb") as f:
                f.write(spectra)

            info(f"Saved to {path_to_file}.")

        except Exception as e:
            error(f"(in take_spectra) {e}")
            return e

        return True

    def take_validation(self, request, path_to_file):
        try:
            self.VM_enable(True)

            spectrum = self.VM_measure(RadiometerEntranceType.IRRADIANCE, 
                    ValidationModuleLightType.LIGHT_VIS, 0, 1.0)

            info("{spectra}")

            spectrum = spectrum.getBytes()
            with open(path_to_file, "wb") as f:
                f.write(spectrum)

            self.VM_enable(False)

        except Exception as e:
            error(f"(in take validation) {e}")


    def get_serials(self):
        try:
            debug("Getting SN")
            instrument = self.hw_info.instrument_serial_number
            visible = self.hw_info.vis_serial_number
            swir = self.hw_info.swir_serial_number
            vm = self.hw_info.vm_serial_number
            return instrument, visible, swir, vm

        except Exception as e:
            error(f"{e}")
            return e


    def get_firmware_versions(self):
        try:
            debug("Getting FW versions")
            instrument_FW_major = self.hw_info.firmware_version_major
            instrument_FW_minor = self.hw_info.firmware_version_minor
            instrument_FW_rev = self.hw_info.firmware_version_revision
            vm_FW_major = self.hw_info.vm_firmware_version_major
            vm_FW_minor = self.hw_info.vm_firmware_version_minor
            vm_FW_rev = self.hw_info.vm_firmware_version_revision
             
            return (instrument_FW_major, instrument_FW_minor, 
                    instrument_FW_rev, vm_FW_major, vm_FW_minor, vm_FW_rev)

        except Exception as e:
            error(f"{e}")
            return e

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

    parser.add_argument("-l", "--loglevel", type=str,
                        help="Verbosity of the instrument driver log",
                        choices=[HypstarLogLevel.ERROR.name,
                                 HypstarLogLevel.INFO.name,
                                 HypstarLogLevel.DEBUG.name,
                                 HypstarLogLevel.TRACE.name], default="ERROR")

    parser.add_argument("-b", "--baudrate", type=int,
                    help="Serial port baud rate used for communications with instrument", # noqa
                    default=115200)

    from logging import basicConfig, DEBUG
    basicConfig(level=DEBUG)

    args = parser.parse_args()

    if args.radiometer and not args.entrance:
        parser.error(f"Please select an entrance for the {args.radiometer}.")

    if args.entrance and not args.radiometer:
        parser.error(f"Please select a radiometer for {args.entrance}.")

    instrument_instance = \
        HypstarHandler(expect_boot_packet=False,
                       instrument_loglevel=HypstarLogLevel[args.loglevel.upper()], # noqa
                       instrument_baudrate=args.baudrate)

    if args.picture:
        request = Request.from_params(args.count, "picture")
        instrument_instance.take_request(request)
        exit(0)

    measurement = args.radiometer, args.entrance, args.it_vnir, args.it_swir
    request = Request.from_params(args.count, *measurement)
    instrument_instance.take_request(request)
