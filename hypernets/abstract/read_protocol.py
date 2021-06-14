#!/usr/bin/python3

"""
Author : alexandre.corizzi@obs-vlfr.fr (LOV)

Spectra name : AA_BBB_CCCC_D_EEEE_FFF_GGG_HHHH_II_JJJJ.spe

A : iterator over "the sequence repeat time"
B : Number of the line in the sequence file (csv file)
C : azimuth pointing angle
D : reference for the azimuth angle
E : zenith pointing angle
F : mode
G : action
H : integration time
I : number of scan in the serie
J : serie time
.spe : extension

with :

D (reference) :
0 = abs
1 = nor
2 = sun

F (mode) :
MODE_NONE  : 0x00 (000)
MODE_SWIR  : 0X40 (064)
MODE_VIS   : 0x80 (128)
MODE_BOTH  : 0xC0 (192)

G (action) :
ACTION_BLACK : 0x00   (00)
ACTION_RAD   : 0x10   (16)
ACTION_IRR   : 0x08   (08)
ACTION_CAL   : 0x01   (01)
ACTION_PIC   : 0x02   (02)
ACTION_NONE  : 0x03   (03)
"""

import csv
from textwrap import dedent
from datetime import datetime, timedelta
from os import mkdir, chdir, listdir, path
from shutil import copy, copyfileobj
from random import random, shuffle, choice

from hypernets.abstract.create_metadata import metadata_header_base


def create_seq_name(now, prefix="SEQ", fmt="%Y%m%dT%H%M%S"):
    return now.strftime(prefix + fmt)


def create_block_position_name(iter_line, line, iter_scheduler=1):
    """
    OUT : [1_90_0_180]
    """

    ref_dict = {'abs': 0, 'nor': 1, 'sun': 2}
    azi, ref, zen, _, action, _, _, _ = line

    block_position = "{:0=2d}".format(iter_scheduler) + '_'
    block_position += "{:0=3d}".format(int(float(iter_line))) + '_'
    block_position += "{:0=4d}".format(int(float(azi))) + '_'
    block_position += str(ref_dict[ref]) + '_'
    block_position += "{:0=4d}".format(int(float(zen)))

    return block_position


def create_spectra_name(line, iter_scheduler=1):
    """
    OUT :
    """

    _, _, _, mode, action, integration, repeat, time = line

    dict_mode = {'non': 0x00, 'swi': 0x40, 'vis': 0x80, 'bot': 0xC0}

    dict_action = {'bla': 0x00, 'rad': 0x10, 'irr': 0x08,
                   'cal': 0x01, 'pic': 0x02, 'non': 0x03}

    spectra_name = '_'
    spectra_name += "{:0=3d}".format(int(dict_mode[mode])) + '_'
    spectra_name += "{:0=2d}".format(int(dict_action[action])) + '_'
    spectra_name += "{:0=4d}".format(int(float(integration))) + '_'
    spectra_name += "{:0=2d}".format(int(float(repeat))) + '_'
    spectra_name += "{:0=4d}".format(int(float(time)))

    return spectra_name


def read_protocol_line(iter_line, now, line, mdfile):
    """
    IN : 045.00,sun,100.00,vis,rad,0,3,0
    """
    pan, ref, tilt, mode, action, _, repeat, _ = line

    block_position = create_block_position_name(iter_line, line)
    mdfile.write("[%s]\n" % block_position)

    if action in ["irr", "rad", "bla"]:

        spectra_name = block_position + create_spectra_name(line) + ".spe"

        spectraVis = []
        spectraSwi = []

        if mode == "vis" or mode == "bot":
            spectraVis = [choice(listdir("../ressources/vis/" + action))
                          for _ in range(int(repeat))]

            spectraVis = ["../ressources/vis/" + action + '/' + f
                          for f in spectraVis]

        if mode == "swi" or mode == "bot":
            spectraSwi = [choice(listdir("../ressources/swi/" + action))
                          for _ in range(int(repeat))]

            spectraSwi = ["../ressources/swi/" + action + '/' + f
                          for f in spectraSwi]

        spectraFiles = spectraVis + spectraSwi
        shuffle(spectraFiles)

        with open("RADIOMETER/" + spectra_name, 'wb') as spectraOut:
            for spectraIn in spectraFiles:
                spectraIn = open(spectraIn, 'rb')
                copyfileobj(spectraIn, spectraOut)

        mdfile.write(spectra_name + "=" + now.strftime("%Y%m%dT%H%M%S") + '\n')

    elif action == "pic":
        copy("../ressources/opensourcesea.jpg", "RADIOMETER/" +
             block_position + ".jpg")

        mdfile.write(block_position + ".jpg=" +
                     now.strftime("%Y%m%dT%H%M%S") + '\n')

    # XXX : action both ??
    elif action == "non" or action == "bot":
        pass

    else:
        print("Error : Action must be 'irr', 'rad', 'bot', 'bla' or 'pic'")

    pan = float(pan)
    tilt = float(tilt)

    # asked pt
    mdfile.write("pt_ask=%s; %s\n" %
                 ("{:.2f}".format(pan), "{:.2f}".format(tilt)))

    # absolute pt
    if ref == "abs" or ref == "nor" or ref == "sun":
        mdfile.write("pt_abs=%s; %s\n" %
                     ("{:.2f}".format(pan), "{:.2f}".format(tilt)))

    pan = pan + (random() - .5) / 2
    tilt = tilt + (random() - .5) / 2

    # reference pt
    mdfile.write("pt_ref=%s; %s\n" %
                 ("{:.2f}".format(pan), "{:.2f}".format(tilt)))

    mdfile.write('\n')


def create_meteo(start, now, meteofile):
    """
    OUT :
    20200420 182201 53.6 20.93 1025.35 12.40
    20200420 182211 53.3 21.01 1025.37 12.20
    ...
    """

    interval = 10  # Measures every 10 seconds
    N = int((now - start).seconds / interval)

    humi = [int(100 * (random()*40+40))/100 for _ in range(N)]
    temp = [int(100 * (random()*6+18))/100 for _ in range(N)]
    pres = [int(100 * (random()*200+900))/100 for _ in range(N)]
    light = [int(100 * (random()*4 + 8))/100 for _ in range(N)]

    for i, v in enumerate(zip(humi, temp, pres, light)):
        meteofile.write("%s %f %f %f %f\n" %
                        ((start + timedelta(seconds=i*interval))
                         .strftime("%Y%m%d %H%M%S"), *v))


def pt_speed(pan_p, tilt_p, pan, tilt, v=5):
    return max(abs(pan_p-pan), abs(tilt_p-tilt)) * 1. / v


def read_protocol_file(protocol_file):
    """
    main function
    """

    now = datetime.now()
    start = now

    seq_name = create_seq_name(now)

    mkdir(seq_name)

    copy(protocol_file, seq_name + '/' + path.basename(protocol_file),
         follow_symlinks=True)

    mkdir(seq_name + "/WEBCAM")
    mkdir(seq_name + "/RADIOMETER")
    mkdir(seq_name + "/METEO")

    chdir(seq_name)

    mdfile = open("metadata.txt", "w")
    mdfile.write(dedent(metadata_header_base(now, protocol_file)))

    with open(path.basename(protocol_file)) as protocol:
        protocol_reader = csv.reader(protocol)
        next(protocol_reader)  # skip the header
        pan_p, tilt_p = 0, 0
        for i, line in enumerate(protocol_reader):
            # strip leading and trailing spaces
            line = [a.strip() for a in line]

            read_protocol_line(i, now, line, mdfile)

            # Time step forward according to the pt speed
            pan, _, tilt, _, _, _, _, _ = line
            pan, tilt = float(pan), float(tilt)
            now = now + timedelta(seconds=pt_speed(pan_p, tilt_p, pan, tilt))
            pan_p, tilt_p = pan, tilt

    mdfile.close()

    # Take a webcam image before and after
    copy("../ressources/webcam.jpg", "WEBCAM/" +
         start.strftime("%Y%m%dT%H%M%S")+".jpg")
    copy("../ressources/webcam.jpg", "WEBCAM/" +
         now.strftime("%Y%m%dT%H%M%S")+".jpg")

    # Meteo simulation
    meteofile = open("METEO/meteo.csv", "w")
    create_meteo(start, now, meteofile)
    meteofile.close()

    # Back to the script path
    chdir('../')


if __name__ == '__main__':
    from time import sleep
    # read_protocol_file("sequence_test.csv")
    read_protocol_file("ressources/sequences_samples/sequence_land_STD.csv")
    sleep(1)
    read_protocol_file("ressources/sequences_samples/sequence_water_1_RD.csv")
    sleep(1)
    read_protocol_file("ressources/sequences_samples/sequence_water_1_STD.csv")
