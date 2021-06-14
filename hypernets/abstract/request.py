
from enum import IntEnum

from hypernets.scripts.libhypstar.python.data_structs.spectrum_raw import \
    RadiometerType, RadiometerEntranceType


class RadiometerExt(IntEnum):
    NONE = 0


class EntranceExt(IntEnum):
    NONE = -1
    PICTURE = 3


class Request(object):
    def __init__(self):
        self.total_measurement_time = 0

    def __str__(self):
        output_str = f"{self.number_cap}."

        if self.radiometer == RadiometerExt.NONE:
            output_str += "picture"

        else:
            output_str += f"{self.radiometer.name}.{self.entrance.name}."
            output_str += f"{self.it_vnir}.{self.it_swir}"
            # output_str += f"{self.total_measurement_time}"

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

        if measurement == ("picture",):
            request.radiometer = RadiometerExt.NONE
            request.entrance = EntranceExt.PICTURE
            return request

        else:
            # TODO : manage different type of params
            rad, ent, it_vnir, it_swir = measurement

            request.radiometer, request.entrance = \
                Request.mode_action_to_radiometer_entrance(rad, ent)

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
               'pic': EntranceExt.PICTURE,
               'non': EntranceExt.NONE}[action.lower()]

        return rad, ent
