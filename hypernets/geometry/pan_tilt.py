#!/usr/bin/python

"""
Move pan-tilt (hypernets tool suit)
# TODO : add log output
"""

from argparse import ArgumentTypeError, ArgumentParser

from serial import Serial
from struct import unpack, pack
from time import sleep  # noqa

from logging import debug, info, warning, error


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


def one_turn_pan(ser):
    data = bytearray([0xFF, 0x01, 0x00, 0x04, 0x01, 0x00])  # XXX: CF doc pelco
    info(f"Query one turn pan : {stringifyBinaryToHex(data)}")
    send_trame(data, ser)


def send_trame(data, ser):
    data = add_checksum(data)
    ser.flush()
    ser.write(data)
    # TODO : Make return


def check_trame(data):
    if len(data) != 7:
        if len(data) == 0:
            warning("Timeout !")
        else:
            warning("Bad length !")
        return False

    if sum(data[1:-1]) % 256 != data[-1]:
        debug(f"Pan-Tilt answer: {stringifyBinaryToHex(data)}")
        warning("Bad Checksum !")
        return False
    return True


def query_position(ser):
    data = bytearray([0xFF, 0x01, 0x00, 0x51, 0x00, 0x00])
    send_trame(data, ser)
    debug(f"Query pan : {stringifyBinaryToHex(data)}")

    data = bytearray()
    for _ in range(7):
        data += ser.read()

    if not check_trame(data):
        sleep(.5)
        return

    _, _, _, cmd, pan, _ = unpack('>BBBBHB', data)

    # convert unsigned to signed if over 400 deg
    # otherwise slightly negative would be around 655 deg
    if pan > 40000:
        pan = -(pan & 0x8000) | (pan & 0x7fff)

    data = bytearray([0xFF, 0x01, 0x00, 0x53, 0x00, 0x00])
    send_trame(data, ser)
    debug(f"Query tilt : {stringifyBinaryToHex(data)}")

    data = bytearray()
    for _ in range(7):
        data += ser.read()

    if not check_trame(data):
        sleep(.5)
        return

    _, _, _, cmd, tilt, _ = unpack('>BBBBHB', data)

    # convert unsigned to signed if over 400 deg
    # otherwise slightly negative would be around 655 deg
    if tilt > 40000:
        tilt = -(tilt & 0x8000) | (tilt & 0x7fff)

    return pan, tilt


def print_position(ser):

    if ser is None:
        ser = open_serial()

    position = query_position(ser)
    if position is not None:
        print(f"Absolute positions: pan {position[0]/100}, "
            f"tilt {position[1]/100}")
    else:
        print("Failed to read current position from pan-tilt!")


def move_to(ser, pan, tilt, wait=False):

    if ser is None:
        ser = open_serial()

    if pan is None or tilt is None:
        initial_position = query_position(ser)
        if pan is None:
            pan = initial_position[0] / 100
        if tilt is None:
            tilt = initial_position[1] / 100

    # Conversion FIXME : here modulo should fit pan/tilt range specification
    debug(f"Before modulo: {pan}, {tilt}")
    pan, tilt = int(pan*100) % 36000, int(tilt*100) % 36000
    debug(f"After modulo: {pan}, {tilt}")

    info(f"Requested Position :\t({pan}, {tilt})\t(10^-2 degrees)")

    if wait:
        initial_position = query_position(ser)
        estimated_time = pt_time_estimation(initial_position, (pan, tilt))

        debug(f"Initial position :\t{initial_position}\t(10^-2 degrees)")
        debug(f"Estimated Time : \t{estimated_time}s")

    # Sync Byte + address + cmd1 + pan
    data = bytearray([0xFF, 0x01, 0x00, 0x4b]) + pack(">H", pan)
    debug("Pan Request :\t%s" % stringifyBinaryToHex(data))
    send_trame(data, ser)

    # Sync Byte + address + cmd1 + tilt
    data = bytearray([0xFF, 0x01, 0x00, 0x4d]) + pack(">H", tilt)
    debug("Tilt Request :\t%s" % stringifyBinaryToHex(data))
    send_trame(data, ser)

    if wait:
        # sleep(estimated_time)
        # for _ in range(int(estimated_time) * 2):
        # FIXME : if problem, low up the precision
        time_to_wait = 1
        for _ in range(34):  # Wait MAX in second) (TODO : time the max)
            sleep(time_to_wait / 2)
            position_0 = query_position(ser)
            sleep(time_to_wait / 2)
            position_1 = query_position(ser)
            if position_0 is not None and position_1 is not None:
                debug(f"Position 0 : {position_0[0]/100}, {position_0[1]/100}")
                debug(f"Position 1 : {position_1[0]/100}, {position_1[1]/100}")
                debug("Estimated velocity : ")
                debug(f"pan : {.02 * (position_1[0] - position_0[0])}, "
                      f"tilt : {.02 * (position_1[1] - position_0[1])} "
                      "(degrees.s^-1)")
                debug("-"*60)

            if position_0 is not None and position_1 is not None and (
                    position_0 == position_1 or
                    # TODO : find a better metric
                    (abs(position_0[0] - position_1[0]) <= 10 and
                     abs(position_0[1] - position_1[1]) <= 10)):
                break

        final_position = query_position(ser)
        info(f"Final position :\t{final_position}\t(10^-2 degrees)")
        ser.close()
        return final_position


def move_to_geometry(geometry, wait=False):
    return move_to(None, geometry.pan_abs, geometry.tilt_abs, wait=wait)


def open_serial():

    pantilt_port = "/dev/ttyS3"

    try:
        from configparser import ConfigParser
        config = ConfigParser()
        config.read("config_dynamic.ini")
        pantilt_port = config["pantilt"]["pantilt_port"]

    except KeyError as key:
        warning(f" {key} default values loaded ({pantilt_port}.")

    except Exception as e:
        error(f"Config Error: {e}.")

    debug(f"Initialization serial port communication on: {pantilt_port}...")
    ser = Serial(port=pantilt_port, baudrate=2400, bytesize=8,
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

    from logging import DEBUG, basicConfig

    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%Y-%m-%dT%H:%M:%S'

    parser = ArgumentParser()

    # TODO add only request pan or tilt
    # mode = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument("-p", "--pan", type=restricted_float,
                        help="set pan (azimuth angle in degrees)",
                        metavar="{0..360}")

    parser.add_argument("-t", "--tilt", type=restricted_float,
                        help="set tilt (zenith angle in degrees)",
                        metavar="{0..360}")

    parser.add_argument("-g", "--get", action="store_true",
                        help="read and print pan/tilt real position")

    parser.add_argument("-w", "--wait", action="store_true",
                        help="wait for pan/tilt end of move and return"
                             " real position")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print extra information")

    args = parser.parse_args()

    if args.verbose:
        basicConfig(level=DEBUG, format=log_fmt, datefmt=dt_fmt) # noqa

    # FIXME
    ser = open_serial()

    if args.get:
        print_position(ser)
    else:
        print(move_to(ser, args.pan, args.tilt, wait=args.wait))
  
    ser.close()
