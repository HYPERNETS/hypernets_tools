#!/usr/bin/python

from datetime import datetime
from struct import unpack, calcsize


class Spectrum(object):
    def __init__(self, data, verbose=True):
        self.headerDef = [("Total Dataset Length", 'H', None),
                          ("Spectrum Type Information", 'B', self.read_spectrum_info),  # noqa
                          ("Timestamp", 'Q', self.read_timestamp),
                          ("Exposure Time", 'H', None),
                          ("Temperature", 'f', None),
                          ("Pixel Count", 'H', None),
                          ("mean X", 'h', None),
                          ("std X", 'h', None),
                          ("mean Y", 'h', None),
                          ("std Y", 'h', None),
                          ("mean Z", 'h', None),
                          ("std Z", 'h', None)]

        # concat all formats together
        headerFormat = '<' + "".join(fmt for _, fmt, _ in self.headerDef)
        # compute size of the whole header
        headerSize = calcsize(headerFormat)
        header = unpack(headerFormat, data[:headerSize])

        for definition, value in zip(self.headerDef, header):
            post_process = definition[2]
            if post_process is not None:
                value = post_process(value)
            if verbose:
                print(f"{definition[0]} : {value}")
        if verbose:
            print("-" * 80)

        # Header expansion
        self.total, self.spec_type, self.timestamp, self.exposure_time,\
            self.temperature, self.pixel_count, self.mean_X, self.std_X,\
            self.mean_Y, self.std_Y, self.mean_Z, self.std_Z = header

        # Read raw counts
        self.counts = unpack('<' + self.pixel_count * 'H',
                             data[headerSize:headerSize+self.pixel_count*2])

        self.crc = unpack('<I', data[headerSize+self.pixel_count*2:
                                     headerSize+self.pixel_count*2+4])

    @staticmethod
    def read_spectrum_info(spec_type: int):
        optic = (spec_type >> 3) & 0x03
        radiometer = (spec_type >> 6) & 0x03
        entranceType = {0x02: "RADIANCE", 0x01: "IRRADIANCE", 0x00: "DARK"}
        radiometerType = {0x02: "VIS", 0x01: "SWIR", 0x03: "BOTH"}

        try:
            spec_type_str = radiometerType[radiometer], entranceType[optic]

        except KeyError:
            spec_type_str = "Error", "Error"

        return spec_type_str

    @staticmethod
    def read_timestamp(timestamp):
        return datetime.utcfromtimestamp(int(timestamp/1000))
