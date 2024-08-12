
from enum import IntEnum
from datetime import datetime, timezone

from hypernets.hypstar.libhypstar.python.data_structs.spectrum_raw import \
    RadiometerType, RadiometerEntranceType

class RadiometerExt(IntEnum):
    NONE = 0


class EntranceExt(IntEnum):
    NONE = -1
    PICTURE = 3
    VM = 4

# KL: duplicate EntranceExt just in case, for IDK what it does
class InstrumentAction(IntEnum):
    NONE = -1
    MEASUREMENT = 1
    PICTURE = 3
    VALIDATION = 4

class Request(object):
    def __init__(self):
        self.total_measurement_time = 0
        self.it_vnir = 0
        self.it_swir = 0
        self.radiometer = None
        self.entrance = None
        self.action = InstrumentAction.NONE
        self.vm_current_ma = 1000 #current in milliamps (to avoid messing with unpacking formats for sequence files)

    def __str__(self):
        if self.entrance == EntranceExt.NONE and self.number_cap == 0:
            return chr(8709)

        output_str = f"{self.number_cap}."

        if self.action == InstrumentAction.PICTURE:
            output_str += "picture"
            return output_str
        elif self.action == InstrumentAction.VALIDATION:
            output_str += "VAL."
        output_str += f"{self.radiometer.name}.{self.entrance.name}."
        output_str += f"{self.it_vnir}.{self.it_swir}"
            # output_str += f"{self.total_measurement_time}"

        if self.action == InstrumentAction.VALIDATION:
            output_str += f".{self.vm_current_ma}"
        return output_str

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_line(cls, line):
        request = cls()
        request.radiometer, request.entrance = \
            Request.mode_action_to_radiometer_entrance(line[0], line[1])

        request.it_vnir = int(line[2])  # protocol v1 doesnt deal with
        request.it_swir = int(line[2])  # different ITs for vnir and swir

        request.number_cap = int(line[3])
        request.total_measurement_time = int(line[4])
        return request

    @classmethod
    def from_params(cls, number_cap, *measurement):

        request = cls()
        request.number_cap = int(number_cap)

        if measurement == ("picture", ):
            request.radiometer = RadiometerExt.NONE
            request.entrance = EntranceExt.PICTURE
            request.action = InstrumentAction.PICTURE
            return request

        elif measurement[0] == "validation":
            request.radiometer = RadiometerExt.NONE
            request.entrance = EntranceExt.VM
            request.action = InstrumentAction.VALIDATION
            measurement = measurement[1:]   # drop action info, we can then parse reminder same way as for simple measurement

            # if we have specific VM current requested, drop that from tuple so we can use default processing
            if len(measurement) > 4:
                request.vm_current_ma = measurement[4]
                measurement = measurement[:4]
        else:
            # TODO : manage different type of params (KL: ?)
            request.action = InstrumentAction.MEASUREMENT

        rad, ent, it_vnir, it_swir = measurement
        request.radiometer, request.entrance = \
                Request.mode_action_to_radiometer_entrance(rad, ent)

        if request.action == InstrumentAction.VALIDATION:
            if request.radiometer == RadiometerType.SWIR or \
                    request.radiometer == RadiometerType.BOTH:
                raise ValueError(f"SWIR validation not supported yet")
            if request.entrance == RadiometerEntranceType.DARK:
                raise ValueError(f"Dark validation measurement does not make sense")

        request.it_vnir = int(it_vnir)
        request.it_swir = int(it_swir)

        return request

    @staticmethod
    def mode_action_to_radiometer_entrance(mode, action):
        rad = {'vis': RadiometerType.VIS_NIR,
               'swi': RadiometerType.SWIR,
               'bot': RadiometerType.BOTH,
               'vnir': RadiometerType.VIS_NIR,
               'swir': RadiometerType.SWIR,
               'both': RadiometerType.BOTH,
               'non': RadiometerExt.NONE}[mode.lower()]

        ent = {'rad': RadiometerEntranceType.RADIANCE,
               'irr': RadiometerEntranceType.IRRADIANCE,
               'bla': RadiometerEntranceType.DARK,
               'dark': RadiometerEntranceType.DARK,
               'dar': RadiometerEntranceType.DARK,
               'pic': EntranceExt.PICTURE,
               'non': EntranceExt.NONE}[action.lower()]

        return rad, ent

    def spectra_name_convention(self, prefix=None):

        dict_radiometer = {RadiometerExt.NONE: 0x00,
                           RadiometerType.SWIR: 0x40,
                           RadiometerType.VIS_NIR: 0x80,
                           RadiometerType.BOTH: 0xC0}

        dict_entrance = {RadiometerEntranceType.DARK: 0x00,
                         RadiometerEntranceType.RADIANCE: 0x10,
                         RadiometerEntranceType.IRRADIANCE: 0x08,
                         EntranceExt.PICTURE: 0x02,
                         EntranceExt.VM: 0x04,
                         EntranceExt.NONE: 0x03}

        # EntranceExt.CALIBRATION: 0x01,

        if prefix is None:
            prefix = self.make_datetime_name(extension="")

        if self.entrance == EntranceExt.PICTURE:
            return prefix + ".jpg"

        spectra_name = prefix + '_'
        spectra_name += "{:0=3d}".format(int(dict_radiometer[self.radiometer]))
        spectra_name += '_'
        spectra_name += "{:0=2d}".format(int(dict_entrance[self.entrance]))
        spectra_name += '_'
        spectra_name += "{:0=4d}".format(self.it_vnir)
        spectra_name += '_'
        # spectra_name += "{:0=4d}".format(int(float(self.it_vnir)) # XXX To
        # spectra_name += '_'                                       # discuss
        spectra_name += "{:0=2d}".format(self.number_cap)
        spectra_name += '_'
        spectra_name += "{:0=4d}".format(self.total_measurement_time)
        spectra_name += ".spe"

        return spectra_name

    @staticmethod
    def make_datetime_name(extension=".jpg"):
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + extension
