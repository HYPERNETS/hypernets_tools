#!/usr/bin/python

"""
Move pan-tilt (hypernets tool suit)
# TODO : add log output
"""

from argparse import ArgumentTypeError, ArgumentParser

from serial import Serial
from struct import unpack, pack
from time import sleep  # noqa
from datetime import datetime, timezone

from logging import debug, info, warning, error


class NoGoZoneError(Exception):
    pass


def pt_time_estimation(position_0, position_1,
                       pan_speed=20.0, tilt_speed=6.0, unit=1e-2):
    """
    Estimation of time to go from position_0 to position_1

    Pan switches direction at 0, tilt at 180, i.e tilt
    movement from 180.00 to 180.01 makes full rotation.

    Time estimation accounts for rotation direction as much
    as possible, but due to backlash and tolerances
    e.g. pan = 0 can also mean pan = 360.

    Rotation speeds depend on supply voltage, defaults are rather conservative.
    Does not account for acceleration/deceleration.
    """
    if position_0 is None or position_1 is None:
        return

    pan0, tilt0 = position_0
    pan1, tilt1 = position_1
    
    if pan1 is None:
        pan_time = 0
    else:
        pan_time = abs(pan1 - pan0) / pan_speed

    if tilt1 is None:
        tilt_time = 0
    else:
        if ((tilt0 <= 18000 and tilt1 > 18000) or
            (tilt1 <= 18000 and tilt0 > 18000)):
            tilt_time = abs((tilt1 + 17999) % 36000 - (tilt0 + 17999) % 36000) / tilt_speed
        else:
            tilt_time = abs(tilt1 - tilt0) / tilt_speed

    return unit * max(pan_time, tilt_time)


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

    debug(f"Pan-Tilt answer: {stringifyBinaryToHex(data)}")

    if sum(data[1:-1]) % 256 != data[-1]:
        warning("Bad Checksum !")
        return False
    return True


def query_position(ser):
    data = bytearray([0xFF, 0x01, 0x00, 0x51, 0x00, 0x00])
    send_trame(data, ser)
    debug(f"Query pan : {stringifyBinaryToHex(data)}")

    data = ser.read(7)

    if not check_trame(data):
        return

    _, _, _, _, pan, _ = unpack('>BBBBHB', data)

    # convert unsigned to signed if over 400 deg
    # otherwise slightly negative would be around 655 deg
    if pan > 40000:
        pan = -(pan & 0x8000) | (pan & 0x7fff)

    data = bytearray([0xFF, 0x01, 0x00, 0x53, 0x00, 0x00])
    send_trame(data, ser)
    debug(f"Query tilt : {stringifyBinaryToHex(data)}")

    data = ser.read(7)

    if not check_trame(data):
        return

    _, _, _, _, tilt, _ = unpack('>BBBBHB', data)

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


def move_to(ser, pan=None, tilt=None, wait=False, tilt_limiter=True):

    if ser is None:
        ser = open_serial()

    if pan is None and tilt is None:
        return

    # Conversion FIXME : here modulo should fit pan/tilt range specification
    debug(f"Before modulo: {pan}, {tilt}")
    if pan is not None:
        pan = round(pan * 100) % 36000
        # workaround for buggy positioner firmware which does not accept
        # 0xFF byte in the request
        if pan & 0xff == 0xff:
            debug(f"pan was {pan:#x}, adding 0.01")
            pan += 1

        if (((pan & 0xff00) >> 8) + pan & 0xff) & 0xff == 0xb3:
            debug(f"pan request checksum would be 0xff, adding 0.01")
            pan += 1

    if tilt is not None:
        tilt = round(tilt * 100) % 36000
        # workaround for buggy positioner firmware which does not accept
        # 0xFF byte in the request
        if tilt & 0xff == 0xff:
            debug(f"tilt was {tilt:#x}, adding 0.01")
            tilt += 1

        if (((tilt & 0xff00) >> 8) + tilt & 0xff) & 0xff == 0xb1:
            debug(f"tilt request checksum would be 0xff, adding 0.01")
            tilt += 1

    debug(f"After modulo: {pan}, {tilt}")

    info(f"Requested Position :\t({pan}, {tilt})\t(10^-2 degrees)")

    # Tilt no-go-zone: abs_deg (130.0, 181.0); abs_tilt (13000, 18100)
    if tilt_limiter is True and tilt is not None and tilt > 13000 and tilt < 18010:
        raise NoGoZoneError(f"Requested absolute tilt position {tilt/100:.2f} is in no-go zone (130.0, 181.0) !!")

    if wait:
        initial_position = query_position(ser)
        estimated_time = pt_time_estimation(initial_position, (pan, tilt))

        debug(f"Initial position :\t{initial_position}\t(10^-2 degrees)")
        if estimated_time is not None:
            debug(f"Estimated Time : \t{estimated_time:.1f}s")
        else:
            debug(f"Estimated Time : unknown")

    if pan is not None:
        # Sync Byte + address + cmd1 + pan
        data = bytearray([0xFF, 0x01, 0x00, 0x4b]) + pack(">H", pan)
        send_trame(data, ser)
        debug("Pan Request :\t%s" % stringifyBinaryToHex(data))

    if tilt is not None:
        # Sync Byte + address + cmd1 + tilt
        data = bytearray([0xFF, 0x01, 0x00, 0x4d]) + pack(">H", tilt)
        send_trame(data, ser)
        debug("Tilt Request :\t%s" % stringifyBinaryToHex(data))

    if wait:
        # full tilt rotation takes 65s at 10.8V supply, 58s at 12V
        # estimated_time can be unknown or miscalculated so we can't use that
        max_time_to_wait = 65 # seconds
        start_time = datetime.now(timezone.utc)

        i = 0
        position_0 = None

        while True:
            i += 1
            debug(f"{'-'*29} {i} {'-'*29}")
            position_1 = query_position(ser)
            time_1 = datetime.now(timezone.utc)

            # time is up
            # either we can't get position from the pan-tilt
            # or the supply voltage is very low
            # or the movement is mechanically blocked by something
            if (time_1 - start_time).total_seconds() > max_time_to_wait:
                debug("Movement takes too long, giving up")
                break

            # pan-tilt didn't respond, retry
            if position_1 is None:
                continue

            # no second position yet
            if position_0 is None:
                position_0 = position_1
                time_0 = time_1
                sleep(1)
                continue

            debug(f"Position 0 : {position_0[0]/100}, {position_0[1]/100}")
            debug(f"Position 1 : {position_1[0]/100}, {position_1[1]/100}")
            debug("Estimated velocity : ")
            delta_t = (time_1 - time_0).total_seconds()
            debug(f"pan : {(position_1[0] - position_0[0]) / (100 * delta_t):.1f}, "
                  f"tilt : {(position_1[1] - position_0[1]) / (100 * delta_t):.1f} "
                  "(degrees.s^-1)")

            if (abs(position_0[0] - position_1[0]) <= 20 and
                     abs(position_0[1] - position_1[1]) <= 10):
                debug("Reached the destination")
                debug("-"*60)
                break
            else:
                debug("Not there yet")
                position_0 = position_1
                time_0 = time_1
                sleep(1)
                continue

        info(f"Final position :\t{position_1}\t(10^-2 degrees)")
        ser.close()
        return position_1


def move_to_geometry(geometry, wait=False, tilt_limiter=True):
    return move_to(None, geometry.pan_abs, geometry.tilt_abs, wait=wait, tilt_limiter=tilt_limiter)


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
                 rtscts=False, dsrdtr=False, exclusive=True)

    if(ser.isOpen() == False):
        ser.open()

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
        try:
            print(move_to(ser, args.pan, args.tilt, wait=args.wait))
        except Exception as e:
            error(f"{e}")
  
    ser.close()
