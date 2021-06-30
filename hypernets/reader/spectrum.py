#!/usr/bin/python

from datetime import datetime
from struct import unpack, calcsize

from hypernets.scripts.libhypstar.python.data_structs.spectrum import \
    Spectrum as HySpectrum


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

        self.str = ""

        # concat all formats together
        headerFormat = '<' + "".join(fmt for _, fmt, _ in self.headerDef)

        # compute size of the whole header and unpack it
        headerSize = calcsize(headerFormat)
        header = unpack(headerFormat, data[:headerSize])

        for definition, value in zip(self.headerDef, header):
            post_process = definition[2]
            if post_process is not None:
                value = post_process(value)
            self.str += f"{definition[0]} : {value}\n"

        if verbose:
            print(f"{self}" + "-" * 80)

        # Header expansion
        self.total, self.spec_type, self.timestamp, self.exposure_time,\
            self.temperature, self.pixel_count, self.mean_X, self.std_X,\
            self.mean_Y, self.std_Y, self.mean_Z, self.std_Z = header

        # Read raw counts
        self.counts = unpack('<' + self.pixel_count * 'H',
                             data[headerSize:headerSize+self.pixel_count*2])

        self.crc = unpack('<I', data[headerSize+self.pixel_count*2:
                                     headerSize+self.pixel_count*2+4])

    def __str__(self):
        return self.str

    @staticmethod
    def read_spectrum_info(spec_type: int):
        spec_type = HySpectrum.SpectrumHeader.SpectrumType.parse_raw(spec_type)
        return spec_type.radiometer.name, spec_type.optics.name

    @staticmethod
    def read_timestamp(timestamp):
        return datetime.utcfromtimestamp(timestamp/1000)
