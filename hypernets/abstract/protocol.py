import re
from re import split
from operator import le, ge, lt, gt

from hypernets.abstract.geometry import Geometry
from hypernets.abstract.request import Request, InstrumentAction
from hypernets.hypstar.libhypstar.python.data_structs.spectrum_raw import RadiometerType  # noqa

from logging import debug, info  # noqa


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

    def read_protocol_v2(self, lines):
        # regexes get very complicated very fast
        # especially if comment character is reused as a sequence metaprogramming var indicator
        # I had it implemented in regexes and it took over 1k steps to process correctly
        # In the end it's easier to maintain just python parser
        def split_lines(lines):
            return lines.split("\n")

        def split_geometry(line):
            return [e for e in split(r"\[|\]|@|,", line) if e]

        def split_measurement(line):
            return [e for e in split(r"\.", line) if e]

        def split_flag(line):
            return [e for e in split(r"~|:=", line) if e]

        def parse_chunk(line):
            # New flag Definition
            if not len(line):
                return
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


        # scans in sequence can be 1 measurement per line or 1 complex scan per line
        for line in split_lines(lines):
            line = line.strip()     # remove leading/trailing whitespace
            debug(f"Parsing line : '{line}'")

            # Ignore empty lines
            if not len(line):
                continue
            # Print / Log Comments
            elif line.startswith("#"):
                if not line.startswith("##"):
                    # print comment lines starting with #
                    # don't print double comment lines starting with ##
                    info(f"Comment : {line}")
            else:
                line = line.replace(" ", "")
                # check if we have more than one scan in line
                if line.count("+") > 0:
                    # check if we have '#' in scan definition that is not a meta variable
                    # meta variables are allowed within geometry definition's square brackets
                    # str.find() does not use proper regexes, need re for that
                    match = re.split("#(?!.*?\])", line)
                    if match:
                        # discard everything after comment sign
                        line = match[0]
                    chunks = line.split("+")
                    for c in chunks:
                        debug(f"chunk {c}")
                        parse_chunk(c)
                else:
                    debug(f"line {line}")
                    parse_chunk(line)

    def check_if_instrument_requested(self):
        for _, request_list in self:
            for request in request_list:
                if request.action != InstrumentAction.NONE:
                    info("This protocol requests instrument.")
                    return True
        info("This protocol doesn't request instrument.")
        return False

    def check_if_swir_requested(self):
        for _, request_list in self:
            for request in request_list:
                if request.radiometer == RadiometerType.SWIR or\
                        request.radiometer == RadiometerType.BOTH:
                    info("This protocol has SWIR request.")
                    return True
        info("This protocol doesn't have SWIR request.")
        return False


    def check_if_vm_requested(self):
        for _, request_list in self:
            for request in request_list:
                if request.action == InstrumentAction.VALIDATION:
                    info("This protocol requests validation.\n")
                    return True
        info("This protocol doesn't request validation.\n")
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
