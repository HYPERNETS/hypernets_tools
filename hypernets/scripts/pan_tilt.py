#!/usr/bin/python

"""
Move pan-tilt (hypernets tool suit)
# TODO : add log output
"""

from argparse import ArgumentTypeError, ArgumentParser

from serial import Serial
from struct import unpack, pack
from time import sleep  # noqa


def pt_time_estimation(position_0, position_1,
                       pan_speed=22.5, tilt_speed=6.5, unit=1e-2):
    """
    Estimation of time to go from position_0 to position_1
    FIXME : Does not take into account forbidden angle, and
            rotation direction neither (shortest path is chosen)
            works with
    """
    if position_0 is None or position_1 is None:
        return

    pan0, tilt0 = position_0
    pan1, tilt1 = position_1
    return unit * max(abs(pan1-pan0)/pan_speed, abs(tilt1-tilt0)/tilt_speed)


def stringifyBinaryToHex(data):
    return ":".join("{:02x}".format(c) for c in data)


def add_checksum(data):
    data += pack("B", sum(data[1:6]) % 256)
    return data


def one_turn_pan(ser, verbose=False):
    data = bytearray([0xFF, 0x01, 0x00, 0x04, 0x01, 0x00])  # XXX: CF doc pelco
    if verbose:
        print(f"Query one turn pan : {stringifyBinaryToHex(data)}")
    send_trame(data, ser)


def send_trame(data, ser):
    data = add_checksum(data)
    ser.flush()
    ser.write(data)
    # TODO : Make return


def check_trame(data):
    if len(data) != 7:
        if len(data) == 0:
            print("Timeout !")
        else:
            print("Bad lenght !")

        return False
    if sum(data[1:-1]) % 256 != data[-1]:
        print("Bad Checksum !")
        return False
    return True


def query_position(ser, verbose=False):
    data = bytearray([0xFF, 0x01, 0x00, 0x51, 0x00, 0x00])
    send_trame(data, ser)
    if verbose:
        print(f"Query pan : {stringifyBinaryToHex(data)}")

    data = bytearray()
    for _ in range(7):
        data += ser.read()

    if not check_trame(data):
        return

    _, _, _, cmd, pan, _ = unpack('>BBBBHB', data)

    data = bytearray([0xFF, 0x01, 0x00, 0x53, 0x00, 0x00])
    if verbose:
        print(f"Query tilt : {stringifyBinaryToHex(data)}")
    send_trame(data, ser)

    data = bytearray()
    for _ in range(7):
        data += ser.read()

    if not check_trame(data):
        return

    _, _, _, cmd, tilt, _ = unpack('>BBBBHB', data)

    return pan, tilt


def move_to(ser, pan, tilt, wait=False, verbose=False,
            offset_pan=0, offset_tilt=-60):

    if ser is None:
        ser = open_serial()

    # Orientation
    pan += offset_pan
    tilt -= offset_tilt

    # Conversion FIXME : here modulo should fit pan/tilt range specification
    pan, tilt = int(pan*100) % 36000, int(tilt*100) % 36000

    if verbose:
        print(f"Requested Position :\t({pan}, {tilt})\t(10^-2 degrees)")

    if wait:
        initial_position = query_position(ser)
        estimated_time = pt_time_estimation(initial_position, (pan, tilt))

        if verbose:
            print(f"Initial position :\t{initial_position}\t(10^-2 degrees)")
            print(f"Estimated Time : \t{estimated_time}s")

    # Sync Byte + address + cmd1 + pan
    data = bytearray([0xFF, 0x01, 0x00, 0x4b]) + pack(">H", pan)
    if verbose:
        print("Pan Request :\t%s" % stringifyBinaryToHex(data))
    send_trame(data, ser)

    # Sync Byte + address + cmd1 + tilt
    data = bytearray([0xFF, 0x01, 0x00, 0x4d]) + pack(">H", tilt)
    if verbose:
        print("Tilt Request :\t%s" % stringifyBinaryToHex(data))
    send_trame(data, ser)

    if wait:
        # sleep(estimated_time)
        # for _ in range(int(estimated_time) * 2):
        # FIXME : if problem, low up the precision
        for _ in range(34):  # Wait MAX in second) (TODO : time the max)
            sleep(.5)
            position_0 = query_position(ser)
            sleep(.5)
            position_1 = query_position(ser)
            if verbose and position_0 is not None and position_1 is not None:
                print(f"Position 0 : {position_0[0]/100}, {position_0[1]/100}\n"  # noqa
                      f"Position 1 : {position_1[0]/100}, {position_1[1]/100}\n"  # noqa
                      "Estimated velocity : "
                      f"pan : {.02 * (position_1[0] - position_0[0])}, "
                      f"tilt : {.02 * (position_1[1] - position_0[1])} "
                      "(degrees.s^-1)")
                print("-"*80)

            if position_0 is not None and position_1 is not None and (
                    position_0 == position_1 or
                    # TODO : find a better metric
                    (abs(position_0[0] - position_1[0]) <= 10 and
                     abs(position_0[1] - position_1[1]) <= 10)):
                break

        final_position = query_position(ser)
        if verbose:
            print(f"Final position :\t{final_position}\t(10^-2 degrees)")
        ser.close()
        return final_position


def open_serial():
    # TODO : Read config before!
    ser = Serial(port='/dev/ttyS3', baudrate=2400, bytesize=8,
                 parity='N', stopbits=1, timeout=.2, xonxoff=False,
                 rtscts=False, dsrdtr=False)
    return ser


if __name__ == '__main__':

    def restricted_float(x):
        try:
            x = float(x)

        except ValueError:
            raise ArgumentTypeError("Error : input must be number")

        if x < 0 or x > 360:
            raise ArgumentTypeError("Error : incorrect range (0 - 360)")

        return x

    parser = ArgumentParser()

    # TODO add only request pan tilt
    # mode = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument("-p", "--pan", type=restricted_float,
                        help="set pan (azimuth angle in degrees)",
                        required=True,
                        metavar="{0..360}")

    parser.add_argument("-t", "--tilt", type=restricted_float,
                        help="set tilt (zenith angle in degrees)",
                        required=True,
                        metavar="{0..360}")

    parser.add_argument("-w", "--wait", action="store_true",
                        help="wait for pan/tilt end of move and return"
                             " real position")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print extra information")

    args = parser.parse_args()

    # FIXME
    ser = open_serial()
    move_to(ser, args.pan, args.tilt)
    ser.close()
