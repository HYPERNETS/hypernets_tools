
from re import split
from operator import le, ge, lt, gt

from hypernets.abstract.geometry import Geometry
from hypernets.abstract.request import Request
from hypernets.abstract.request import RadiometerExt, EntranceExt
from hypernets.hypstar.libhypstar.python.data_structs.spectrum_raw import RadiometerType # noqa

from logging import debug, info, warning, error # noqa


class Protocol(list[(Geometry, list[Request])]):
    def __init__(self, filename=None):
        self.name = filename
        self.version = None
        self.flags = dict()

        if self.name is not None:
            with open(filename, 'r') as fd:
                first_line = fd.readline()
                if first_line[:17] == "HypernetsProtocol":
                    self.version = first_line[18:-1]
                    self.read_protocol_v2(fd.read())
                else:
                    self.version = "1"
                    self.read_protocol_v1(fd.readlines())
        else:
            self.name = "On the Fly Protocol"

    def __str__(self):

        protocol_str = "\n"
        for i, (geometry, request) in enumerate(self, start=1):
            protocol_str += f"[{i}] {geometry}\n\t{request}\n\n"

        flags_str = "\n" + "Defined flags : "
        for flag, (var, op, val) in self.flags.items():
            flags_str += f"{flag} := {var} [{op.__name__}] {val}\n\t\t"

        return f"\n==== Protocol version : {self.version} ====\n" + \
            "-"*len(self.name) + f"\n{self.name}\n" + "-"*len(self.name) + \
            f"{protocol_str}" + f"{flags_str}"

    def add_flag(self, flag, definition):
        # We understand formal expressions such as : variable [operator] value.
        def split_flag_definition(definition):
            # with the following operators :
            operators = {"<=": le, "=>": ge, "<": lt, ">": gt}
            regex = r'|'.join(operators.keys())
            var, op, value = [e for e in split(f"({regex})", definition) if e]
            return var, operators[op], int(value)
        # variable, operator, value =
        self.flags[flag] = split_flag_definition(definition)

    def read_protocol_v1(self, lines):

        for line in lines:
            line = [a.strip() for a in line.split(',')]
            pan, ref, tilt, *measurement = line

            if ref == 'sun' and pan == "-1" and tilt == "-1":
                pan, ref, tilt = 0.0, 0, 0.0
            elif ref == 'sun':
                ref = 2
            elif ref == 'abs' or ref == 'nor':
                ref = 8
            else:
                ref = 4

            request = Request.from_line(measurement)
            info(request)
            pan, tilt = float(pan), float(tilt)
            self.append((Geometry(ref, pan=pan, tilt=tilt), [request]))

    def read_protocol_v2(self, lines):
        # FIXME : special caracter in comment leads

        # Some regex defintions :
        def split_lines(lines):
            return [e for e in split(r"\+|\n|\t", lines) if e]

        def split_geometry(line):
            return [e for e in split(r"\[|\]|@|,", line) if e]

        def split_measurement(line):
            return [e for e in split(r"\.", line) if e]

        def split_flag(line):
            return [e for e in split(r"~|:=", line) if e]

        # Split line with '+' as separation character
        for line in split_lines(lines):
            debug(f"Parsing line : {line}")
            # Ignore new lines
            if line.isspace():
                continue

            # Print / Log Comments
            elif line[0] == "#":
                info(f"Comment : {line}")

            else:
                # Remove spaces
                line = line.replace(" ", "")

                # New flag Definition
                if line[0] == "~":
                    self.add_flag(*split_flag(line))

                # New Geometry
                elif line[0] == "@":
                    pan, ref_p, tilt, ref_t, *flags = split_geometry(line)
                    reference = Geometry.reference_to_int(ref_p, ref_t)
                    cur_geo = Geometry(reference, pan, tilt, flags=flags)
                    self.append((cur_geo, list()))

                # New Request : Measurement or Picture
                else:
                    request = Request.from_params(*split_measurement(line))
                    self[-1][1].append(request)

    def check_if_instrument_requested(self):
        for _, request_list in self:
            for request in request_list:
                if request.radiometer != RadiometerExt.NONE or\
                        request.entrance == EntranceExt.PICTURE:
                    info("This protocol requests instrument.")
                    return True
        info("This protocol doesn't request instrument.")
        return False

    def check_if_swir_requested(self):
        for _, request_list in self:
            for request in request_list:
                if request.radiometer == RadiometerType.SWIR or\
                        request.radiometer == RadiometerType.BOTH:
                    info("This protocol has SWIR request.\n")
                    return True
        info("This protocol doesn't have SWIR request.\n")
        return False

    @staticmethod
    def create_seq_name(now, prefix="SEQ", fmt="%Y%m%dT%H%M%S", suffix=""):
        return now.strftime(prefix + fmt + suffix)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-f", "--filename", type=str, required=True,
                        help="Select a protocol file (txt, csv)")

    from logging import basicConfig, DEBUG
    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%H:%M:%S'
    basicConfig(level=DEBUG, format=log_fmt, datefmt=dt_fmt)

    args = parser.parse_args()
    protocol = Protocol(args.filename)
    protocol.check_if_instrument_requested()
    protocol.check_if_swir_requested()
    info(protocol)
