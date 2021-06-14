
from re import split
from hypernets.abstract.geometry import Geometry
from hypernets.abstract.request import Request
from hypernets.scripts.libhypstar.python.data_structs.spectrum_raw import RadiometerType # noqa


class Protocol(list[(Geometry, list[Request])]):
    def __init__(self, filename):
        self.name = filename
        self.version = None

        with open(filename, 'r') as fd:
            first_line = fd.readline()
            if first_line[:17] == "HypernetsProtocol":
                self.version = first_line[18:-1]
                self.read_protocol_v2(fd.read())
            else:
                self.version = "1"
                self.read_protocol_v1(fd.readlines())

    def __str__(self):

        protocol_str = "\n"
        for i, (geometry, request) in enumerate(self, start=1):
            protocol_str += f"{i}, {geometry}, {request}\n"

        return f"==== Protocol version : {self.version} ====\n" + \
            "-"*len(self.name) + f"\n{self.name}\n" + "-"*len(self.name) + \
            f"{protocol_str}"

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
            pan, tilt = float(pan), float(tilt)
            self.append((Geometry(ref, pan=pan, tilt=tilt), [request]))

    def read_protocol_v2(self, lines, print_comment=False):

        def split_lines(lines):
            return [e for e in split(r"\+|\n|\t", lines) if e]

        def split_geometry(line):
            return [e for e in split(r"\[|\]|@|,", line) if e]

        def split_measurement(line):
            return [e for e in split(r"\.", line) if e]

        # Split line with '+' as separation character
        for line in split_lines(lines):

            # Ignore new lines
            if line.isspace():
                continue

            # Print / Log Comments
            elif line[0] == "#":
                print_comment and print(f"{line}")

            else:
                # Remove spaces
                line = line.replace(" ", "")

                # Geometry
                if line[0] == "@":
                    pan, ref_p, tilt, ref_t, *flags = split_geometry(line)
                    ref = Geometry.reference_to_int(ref_p, ref_t)
                    cur_geo = Geometry(ref, pan=pan, tilt=tilt, flags=flags)

                    # print(f"New geometry : {current_geometry}")
                    self.append((cur_geo, list()))

                # Measurement or Picture
                else:
                    request = Request.from_params(*split_measurement(line))
                    self[-1][1].append(request)

    def check_if_swir_requested(self):
        for _, request_list in self:
            for request in request_list:
                if request.radiometer == RadiometerType.SWIR or\
                        request.radiometer == RadiometerType.BOTH:
                    print("Note : This protocol has SWIR request")
                    return True
        print("Note : This protocol doesn't have SWIR request")
        return False


if __name__ == '__main__':
    protocol = Protocol("sequences_samples/sequence_water.txt")
    #  print(protocol)
    protocol.check_if_swir_requested()

    for i, (geometry, requests) in enumerate(protocol, start=1):
        print(f"{i}, {geometry}")
        for request in requests:
            print(request.radiometer, request.entrance)
