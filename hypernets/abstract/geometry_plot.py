
from math import radians, pi
import matplotlib.pyplot as plt

from hypernets.abstract.protocol import Protocol
from hypernets.abstract.geometry import Geometry

from logging import info, debug, basicConfig, DEBUG, INFO  # noqa
from datetime import datetime, timedelta


def daterange(start_time="12:00", end_time="20:00", date="2021-12-21", delta=60):  # noqa
    debug(f"{date}: from {start_time} to {end_time}, every {delta} min.")

    start_time = datetime.strptime(date + start_time, '%Y-%m-%d%H:%M')
    end_time = datetime.strptime(date + end_time, '%Y-%m-%d%H:%M')

    # start_time = datetime.strptime(date + "12:00", '%Y-%m-%d%H:%M')
    # end_time = datetime.strptime(date + "20:00", '%Y-%m-%d%H:%M')
    # delta = timedelta(days=24)

    delta = timedelta(minutes=delta)

    while start_time <= end_time:
        yield start_time
        start_time += delta


def make_pan_tilt_list(geometries, dates):
    points = []
    for n, geometry in enumerate(geometries, start=1):
        info(f"[{n}] : {geometry}")
        pan, tilt = list(), list()
        for now in dates:
            info(f"--> {str(now)}")
            geometry.get_absolute_pan_tilt(now)
            pan.append(geometry.pan_abs)
            tilt.append(geometry.tilt_abs)
        points.append((pan, tilt))
    return points


def plot_polar_pan(fig, dates, pans):
    ax = fig.add_subplot(1, 2, 1, projection='polar')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])

    xT = plt.xticks()[0]
    xL = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    plt.xticks(xT, xL)

    for n, pan in enumerate(pans, start=1):
        pan = list(map(radians, pan))
        plt.scatter(pan, [n for _ in range(len(pan))])

        for i, x in enumerate(pan):
            plt.annotate(dates[i].strftime("%H:%M"), xy=(x, n),
                         arrowprops=dict(width=1, headwidth=1, headlength=1),
                         xytext=(x, 0.1+n+(i*0.9)/len(pan)))

    plt.title("Azimuth")


def plot_cartesian_tilt(fig, dates, tilts):
    import matplotlib.dates as mdates
    ax = fig.add_subplot(1, 2, 2)

    for n, tilt in enumerate(tilts, start=1):
        #  tilt = list(map(lambda x: x, tilt))
        plt.plot(dates, tilt, '-o')

    # ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%d_%H:%M"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.title("Zenith")


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-f", "--filename", type=str, default=None,
                        help="Select a protocol file (txt, csv)")

    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%H:%M:%S'

    # basicConfig(level=INFO, format=log_fmt, datefmt=dt_fmt)
    basicConfig(level=DEBUG, format=log_fmt, datefmt=dt_fmt)

    args = parser.parse_args()

    if args.filename is not None:
        protocol = Protocol(args.filename)

    else:
        protocol = Protocol()
        protocol.append([Geometry(2, pan=-90, tilt=180), list()])
        protocol.append([Geometry(0), list()])

    info(protocol)

    # get one single time each different geometry
    geometries = set([geometry for (geometry, _) in protocol])
    info(f"Protocol has {len(protocol)} lines with different {len(geometries)}"
         f" geometries.")

    dates = list(daterange())
    debug(list(map(str, dates)))

    fig = plt.figure()

    points = make_pan_tilt_list(geometries, dates)
    plot_polar_pan(fig, dates, [pan for pan, _ in points])

    # Shadow for plateform representation
    plt.fill_between([pi/2, 3*pi/4, pi], 0, len(geometries), color="grey", alpha=.8) # noqa

    plot_cartesian_tilt(fig, dates, [tilt for _, tilt in points])

    plt.legend([str(geometry) for geometry in geometries])

    plt.show()
