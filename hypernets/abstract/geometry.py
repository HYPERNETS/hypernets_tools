
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
        str_output += f" --> [{self.pan_abs:.2f} ; {self.tilt_abs:.2f}]"
        str_output += f" -- {self.flags}"
        return str_output

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

    def get_absolute_pan_tilt(self):

        self.pan_abs, self.tilt_abs = self.pan, self.tilt

        pan_ref, tilt_ref = Geometry.int_to_reference(self.reference)

        # Default values :
        offset_pan, offset_tilt, reverse_tilt = 0, 0, False

        # Get offset values :
        if 'sun' in [pan_ref, tilt_ref] or 'hyp' in [pan_ref, tilt_ref]:
            try:
                from configparser import ConfigParser
                config_file = "config_dynamic.ini"
                config = ConfigParser()
                config.read(config_file)
                offset_pan = int(config["pantilt"]["offset_pan"])
                offset_tilt = int(config["pantilt"]["offset_tilt"])
                reverse_tilt = config["pantilt"]["reverse_tilt"] == "yes"

            except KeyError as key:
                print(f"Warning : {key} default values loaded")

            except Exception as e:
                print(f"Config Error : {e}")

            from operator import neg, pos
            reverse_tilt = {True: neg, False: pos}[reverse_tilt]

            # Orientation
            if pan_ref in ['sun', 'hyp']:
                self.pan_abs -= reverse_tilt(offset_pan)

            if tilt_ref in ['sun', 'hyp']:
                self.tilt_abs -= reverse_tilt(offset_tilt)

        # Get sun position
        if 'sun' in [pan_ref, tilt_ref]:  # pickle me :
            from hypernets.geometry.spa.spa_hypernets import spa_from_datetime
            azimuth_sun, zenith_sun = spa_from_datetime(verbose=False)
            zenith_sun = 180 - zenith_sun

            # Point to the sun
            if pan_ref == 'sun':
                self.pan_abs += azimuth_sun

            if tilt_ref == 'sun':
                self.tilt_abs += zenith_sun

        self.tilt_abs = reverse_tilt(self.tilt_abs)
        self.pan_abs = reverse_tilt(self.pan_abs)


if __name__ == '__main__':
    print(Geometry.__doc__)
    print("Ref     Pan    Tilt")
    for ref in range(Geometry.length):
        print(f"{ref}  -> {Geometry.int_to_reference(ref)}")

    # for ref in range(9):
    #     reference = Geometry.int_to_reference(ref)
    #     geometry = Geometry(ref)
    #     print(geometry)
    #     geometry.get_absolute_pan_tilt()
    #     print(geometry)
