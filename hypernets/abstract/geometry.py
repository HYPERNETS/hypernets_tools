
from logging import info, warning, error, debug


class Geometry(object):
    """
    Definitions :

        * Absolute : actual geometry of the pan-tilt

        * Hypernets, such as Hypernets(0, 0) = (south, nadir)

        * Sun : such as Sun(0, 0) = point to the sun

        Every relative pan / tilt relative to azimuth / zenith are defined
        clockwise when positive and counter-clockwise when negative.

    """

    length = 9

    # FIXME : some constant should be here ?
    ref_to_int = dict()

    ref_to_int['sun'] = 0
    ref_to_int['abs'] = 1
    ref_to_int['nor'] = 2
    ref_to_int['hyp'] = 2

    # For V2
    ref_to_int['sun'] = 0
    ref_to_int['abs'] = 1
    ref_to_int['hyper'] = 2
    ref_to_int['north'] = 2

    int_to_ref = dict()
    int_to_ref[0] = 'sun'
    int_to_ref[1] = 'abs'
    int_to_ref[2] = 'hyp'

    def __init__(self, reference: int, pan=0.0, tilt=0.0, flags=[]):
        self.reference = reference
        self.pan = float(pan)
        self.tilt = float(tilt)
        self.flags = flags
        self.pan_abs = 0
        self.tilt_abs = 0

    def __str__(self):
        ref_pan, ref_tilt = Geometry.int_to_reference(self.reference)
        str_output = f"{self.pan:.2f} ({ref_pan}) ; {self.tilt:.2f} ({ref_tilt})" # noqa
        str_output += f" --> [{self.pan_abs:.2f} ; {self.tilt_abs:.2f}] (abs)"
        str_output += f" -- {self.flags}"
        return str_output

    def __eq__(self, other):

        if self.reference != other.reference:
            return False

        if self.pan != other.pan or self.tilt != other.tilt:
            return False

        if self.flags != other.flags:  # TODO : check if always correct
            return False

        return True

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def from_references(cls, ref_pan, ref_tilt, pan=0.0, tilt=0.0, flags=[]):
        reference = Geometry.reference_to_int(ref_pan, ref_tilt)
        return cls(reference, pan=pan, tilt=tilt, flags=flags)

    @staticmethod
    def reference_to_int(pan_ref: str, tilt_ref: str) -> int:
        return \
            Geometry.ref_to_int[tilt_ref] + \
            Geometry.ref_to_int[pan_ref] * 3

    @staticmethod
    def int_to_reference(ref: int) -> str:
        pan_ref, tilt_ref = divmod(ref, 3)
        return Geometry.int_to_ref[pan_ref], Geometry.int_to_ref[tilt_ref]

    def create_block_position_name(self, iter_line, iter_scheduler=1):
        """
        OUT : [1_90_0_180]
        """

        # ref_dict = {'abs': 0, 'nor': 1, 'sun': 2}

        block_position = "{:0=2d}".format(iter_scheduler) + '_'
        block_position += "{:0=3d}".format(iter_line) + '_'
        block_position += "{:0=4d}".format(int(self.pan)) + '_'
        block_position += str(self.reference) + '_'
        block_position += "{:0=4d}".format(int(self.tilt))

        return block_position

    def get_absolute_pan_tilt(self, now=None):
        try:  # FIXME
            from configparser import ConfigParser
            config_file = "config_dynamic.ini"
            config = ConfigParser()
            config.read(config_file)
            offset_pan = float(config["pantilt"]["offset_pan"])
            offset_tilt = float(config["pantilt"]["offset_tilt"])
            reverse_tilt = config["pantilt"]["reverse_tilt"] == "yes"
            azimuth_switch = float(config["pantilt"]["azimuth_switch"])

        except KeyError as key:
            warning(f" {key} default values loaded")
            # Default values :
            # offset_tilt = 0
            offset_pan, reverse_tilt = 0, False
            azimuth_switch = 360

        except Exception as e:
            error(f"Config Error : {e}")

        from operator import neg, pos
        reverse_tilt = {True: neg, False: pos}[reverse_tilt]

        self.pan_abs, self.tilt_abs = self.pan, self.tilt
        pan_ref, tilt_ref = Geometry.int_to_reference(self.reference)


        # Get sun position
        if 'sun' in [pan_ref, tilt_ref]:  # pickle me :
            from hypernets.geometry.spa_hypernets import spa_from_datetime
            azimuth_sun, zenith_sun = spa_from_datetime(now=now)
            zenith_sun = 180 - zenith_sun

            # determine hemisphere
            latitude = float(config["GPS"]["latitude"])
            if latitude >= 0:
                hemisphere_offset = 0
                hemisphere_conv = pos
                hemisphere_txt = "northern"
            else:
                # convert southern hemisphere geometry to northern hemisphere
                # for azimuth_switch check
                hemisphere_offset = 180
                hemisphere_conv = neg
                hemisphere_txt = "southern"

            # Point to the sun
            if pan_ref == 'sun':
                # TODO : move to flag geometry condition
                if (hemisphere_offset + hemisphere_conv(azimuth_sun)) % 360 <= (hemisphere_offset + hemisphere_conv(azimuth_switch)) % 360:
                    debug(f"Sun azimuth ({azimuth_sun:.2f}) has not yet reached the azimuth "
                          f"switch ({azimuth_switch:.2f}) at {hemisphere_txt} hemisphere "
                          f"--> {self.pan_abs:+.2f}°")
                    self.pan_abs = azimuth_sun + self.pan_abs
                else:
                    debug(f"Sun azimuth ({azimuth_sun:.2f}) has passed the azimuth "
                          f"switch ({azimuth_switch:.2f}) at {hemisphere_txt} hemisphere "
                          f"--> {-self.pan_abs:+.2f}°")
                    self.pan_abs = azimuth_sun - self.pan_abs

            if tilt_ref == 'sun':
                self.tilt_abs += zenith_sun

        # Get offset values :
        if 'sun' in [pan_ref, tilt_ref] or 'hyp' in [pan_ref, tilt_ref]:
            # Orientation
            if pan_ref in ['sun', 'hyp']:
                self.pan_abs -= reverse_tilt(offset_pan)
                # self.pan_abs -= offset_pan

            if tilt_ref in ['sun', 'hyp']:
                self.tilt_abs -= reverse_tilt(offset_tilt)

        self.tilt_abs = reverse_tilt(self.tilt_abs)
        if reverse_tilt is neg:
            self.pan_abs = self.pan_abs + 180

        # force to [0...360] range
        self.pan_abs = self.pan_abs % 360
        self.tilt_abs = self.tilt_abs % 360


if __name__ == '__main__':
    from logging import basicConfig, DEBUG
    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%H:%M:%S'
    basicConfig(level=DEBUG, format=log_fmt, datefmt=dt_fmt)

    info(Geometry.__doc__)

    for ref in range(9):
        info(f"[{ref}]  -> {Geometry.int_to_reference(ref)}")
        reference = Geometry.int_to_reference(ref)
        geometry = Geometry(ref)
        info(geometry)
        geometry.get_absolute_pan_tilt()
        info(geometry)

    info("")
    geometry = Geometry(2, pan=90, tilt=40)
    geometry.get_absolute_pan_tilt()
    info(geometry)
