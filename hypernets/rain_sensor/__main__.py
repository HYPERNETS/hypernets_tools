from argparse import ArgumentTypeError, ArgumentParser
from logging import basicConfig, getLogger, info, error  # noqa
from time import sleep
from .rain_sensor import RainSensor
import gpiod


if __name__ == '__main__':
    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%Y-%m-%dT%H:%M:%S'

    parser = ArgumentParser()

    parser.add_argument("-c", "--count", type=int, default=10, 
                    help="How many times to read the rain sensor state")

    parser.add_argument("-l", "--loglevel", type=str,
                        help="Log level",
                        choices=["ERROR", "INFO", "DEBUG"],
                                default="INFO")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--numeric", action="store_true",
                    help="Disable all logging and output only 0 or 1")

    group.add_argument("-s", "--string", action="store_true",
                    help="Print 'Raining' or 'Not raining'")

    args = parser.parse_args()

    basicConfig(level=args.loglevel, format=log_fmt, datefmt=dt_fmt)

    if args.numeric:
        logger = getLogger()
        logger.disabled = True

    try:
        rain_sensor = RainSensor()
    except Exception as e:
        error(f"{e}")
        exit(-1)

    for i in range(args.count):
        try:
            value = int(rain_sensor.read_value())
            info(f"Read value : {value}")
        except Exception as e:
            error(f"{e}")
            exit(-1)

        if args.numeric:
            print(value)

        if args.string:
            str_val = {0: "Not raining", 1: "Raining"}[value]
            print(str_val)

        if i + 1 != args.count:
            sleep(1)

