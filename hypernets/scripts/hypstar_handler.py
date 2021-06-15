
from datetime import datetime
from argparse import ArgumentParser

from hypernets.scripts.libhypstar.python.hypstar_wrapper import Hypstar, wait_for_instrument # noqa

from hypernets.scripts.libhypstar.python.data_structs.spectrum_raw import \
    RadiometerType, RadiometerEntranceType

from hypernets.scripts.libhypstar.python.data_structs.hardware_info import \
    HypstarSupportedBaudRates

from sys import exit

from hypernets.abstract.request import EntranceExt


# TODO : move it to virtual
def make_datetime_name(extension=".jpg"):  # todo : move to virtual
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S") + extension


class HypstarHandler(Hypstar):
    def __init__(self, instrument_port="/dev/radiometer0", # noqa : C901
                 instrument_baudrate=3000000,
                 instrument_loglevel=3,
                 except_boot_packet=True):

        # self.last_it_swir = None
        # self.last_it_vnir = None

        if except_boot_packet is True:
            boot_timeout = 17
            if not wait_for_instrument(instrument_port, boot_timeout):
                # just in case instrument sent BOOTED packet while we were
                # switching baudrates, let's test if it's there
                try:
                    super().__init__(instrument_port)

                except IOError as e:
                    print(f"Error : {e}")
                    print("[ERROR] Did not get instrument BOOTED packet in {}s".format(boot_timeout)) # noqa
                    exit(27)

                except Exception as e:
                    print(f"Error : {e}")

            else:  # We got the boot packet
                try:
                    super().__init__(instrument_port)

                except Exception as e:
                    print(f"Error : {e}")
                    exit(6)

        else:  # no boot packet if expected (gui mode)
            try:
                super().__init__(instrument_port)

            except Exception as e:
                print(f"Error : {e}")
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
                print("[ERROR] MUX+SWIR+TEC hardware not available")
                exit(27)  # SIGABORT

        except IOError as e:
            print(f"Error : {e}")
            exit(6)

        except Exception as e:
            print(e)
            # if instrument does not respond, there's no point in doing
            # anything, so we exit with ABORTED signal so that shell script can
            # catch exception
            exit(6)  # SIGABRT

    def take_picture(self, params=None, path_to_file=None, return_stream=False): # noqa
        # Note : 'params = None' for now, only 5MP is working
        if path_to_file is None:
            from os import path, mkdir
            path_to_file = make_datetime_name()
            if not path.exists("DATA"):
                mkdir("DATA")
            path_to_file = path.join("DATA", path_to_file)

        try:
            self.packet_count = self.capture_JPEG_image(flip=True)
            if not self.packet_count:
                return False
            stream = self.download_JPEG_image()
            with open(path_to_file, 'wb') as f:
                f.write(stream)

            print(f"Saved to {path_to_file}.")
            if return_stream:
                return stream
            return True

        except Exception as e:
            print(f"Error : {e}")
            return e

    def get_serials(self):
        try:
            print("Getting SN")  # LOGME
            instrument = self.hw_info.instrument_serial_number
            visible = self.hw_info.vis_serial_number
            swir = self.hw_info.swir_serial_number
            return instrument, visible, swir

        except Exception as e:
            print(f"Error : {e}")
            return e

    def take_spectra(self, request, path_to_file=None, gui=False):

        # if it_vnir == 0 and ent == RadiometerEntranceType.DARK:
        #     it_vnir == self.last_it_vnir

        # if it_swir == 0 and ent == RadiometerEntranceType.DARK:
        #     it_swir == self.last_it_swir

        if path_to_file is None:
            from os import path, mkdir
            if not path.exists("DATA"):
                mkdir("DATA")
            path_to_file = make_datetime_name(extension=".spe")
            path_to_file = path.join("DATA", path_to_file)

        try:
            # get latest environmental log and print it to output log
            env_log = self.get_env_log()
            print(env_log.get_csv_line(), flush=True)

            capture_count = self.capture_spectra(request.radiometer,
                                                 request.entrance,
                                                 request.it_vnir,
                                                 request.it_swir,
                                                 request.number_cap,
                                                 request.total_measurement_time) # noqa

            slot_list = self.get_last_capture_spectra_memory_slots(
                capture_count)

            cap_list = self.download_spectra(slot_list)

            if len(cap_list) == 0:
                return Exception("Cap list length is zero")

            # Concatenation
            spectra = b''
            for n, spectrum in enumerate(cap_list):
                spectra += spectrum.getBytes()

                # # Read ITs :
                # if spectrum.spectrum_header.spectrum_config.vnir:
                #     self.last_it_vnir = \
                #         spectrum.spectrum_header.integration_time_ms
                #   # print(f"AIT update: {spectrum.radiometer}->{it_vnir} ms")
                # elif spectrum.spectrum_header.spectrum_config.swir:
                #     self.last_it_swir = \
                #         spectrum.spectrum_header.integration_time_ms
                #   # print(f"AIT update: {spectrum.radiometer}->{it_swir} ms")
                #     # XXX --> LOG me

            # Save
            with open(path_to_file, "wb") as f:
                f.write(spectra)

            print(f"Saved to {path_to_file}.")

        except Exception as e:
            print(f"Error (in take_spectra): {e}")
            return e

        if gui:
            # return self.last_it_vnir, self.last_it_swir, path_to_file
            return None, None, path_to_file

        # return it_vnir, it_swir
        return True

    @staticmethod
    def mode_action_to_radiance_entrance(mode, action):
        rad = {'vis': RadiometerType.VIS_NIR, 'swi': RadiometerType.SWIR,
               'bot': RadiometerType.BOTH}[mode]

        ent = {'rad': RadiometerEntranceType.RADIANCE,
               'irr': RadiometerEntranceType.IRRADIANCE,
               'bla': RadiometerEntranceType.DARK}[action]

        return rad, ent


# FIXME : write more generic function (refactor with take_spectra)
# def _cli_extra_parser(args):
#     if args.picture:
#         take_picture(path_to_file=args.output)
#     else:
#         if args.radiometer == 'vnir':
#             mode = "vis"
#         elif args.radiometer == 'swir':
#             mode = "swi"
#         elif args.radiometer == 'both':
#             mode = "bot"
#
#         if args.entrance == 'dark':
#             action = 'bla'
#         else:
#             action = args.entrance
#
#         take_spectra(None, args.output, mode, action,
#                      args.it_vnir, args.it_swir, args.count)


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

#    _cli_extra_parser(args)
