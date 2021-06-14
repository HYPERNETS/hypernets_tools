
class Geometry(object):
    ref_to_int = dict()

    ref_to_int['sun'] = 0
    ref_to_int['abs'] = 1
    ref_to_int['nor'] = 2

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

    def __str__(self):
        ref_pan, ref_tilt = Geometry.int_to_reference(self.reference)
        return f"{self.pan} ({ref_pan}) ; {self.tilt} ({ref_tilt})"

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


if __name__ == '__main__':

    # geometry = Geometry.reference_to_int('sun', 'hyp')
    # print(geometry)

    print("Ref     Pan    Tilt")
    for ref in range(9):
        print(f"{ref}  -> {Geometry.int_to_reference(ref)}")
