#!/usr/bin/python3
# coding: utf-8
from configparser import ConfigParser
from tkinter import E, W, N, S, NE, NW, SE, SW, SE, BOTH, DISABLED, END  # noqa
from tkinter import PhotoImage, Label
from tkinter import Tk

from hypernets.gui.frame_radiometer import FrameRadiometer
from hypernets.gui.frame_pantilt import FramePanTilt
from hypernets.gui.frame_yoctopuce import FrameYoctopuce
from hypernets.gui.frame_webcam import FrameWebcam
from hypernets.gui.frame_console import FrameConsole
from hypernets.gui.frame_rainsensor import FrameRainSensor

from importlib import resources
from logging import basicConfig
from hypernets.resources import img


class Guied(Tk):
    def __init__(self):
        super().__init__()

        self.radiometer = True
        self.pantilt = True
        self.yoctopuce = True
        self.output = True
        self.rainsensor = True
        self.loglevel = "ERROR"
        self.baudrate = 115200
        self.serial_port = "/dev/radiometer0"
        self.tec_target_temp = 0
        self.webcam = False
        self.console = False

        self.read_config()
        self.create_logo()
        self.configure_frames()
        self.configure_gui()
        self.bind('<Control-q>', self.quit_program)

        log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
        dt_fmt = '%Y-%m-%dT%H:%M:%S'

        basicConfig(level=self.verbosity, format=log_fmt, datefmt=dt_fmt)

        self.mainloop()

    def quit_program(self, e):
        # call destructor of the hypstar instance
        if self.frmRadiometer.hypstar is not None:
            del self.frmRadiometer.hypstar

        self.quit()

    def configure_gui(self):
        self.title("Guied - Hypernets GUI")
        # self.geometry('700x550')
        # self.resizable(0, 0)

    def create_logo(self):
        logo_hypernets = resources.files(img).joinpath("logo.png").read_bytes()
        self.img_hyp = PhotoImage(data=logo_hypernets)
        logo_lbl = Label(self, image=self.img_hyp)
        logo_lbl.grid(column=0, row=0, columnspan=2)

    def configure_frames(self):
        if self.radiometer:
            self.frmRadiometer = FrameRadiometer(self)
            self.frmRadiometer.grid(sticky=W+E+N+S, column=0, row=1, padx=2, pady=2,
                               rowspan=4)

        if self.pantilt:
            frmPanTilt = FramePanTilt(self)
            frmPanTilt.grid(sticky=W+E+N+S,    column=1, row=3, padx=2, pady=2)

        if self.yoctopuce:
            frmYocto = FrameYoctopuce(self)
            frmYocto.grid(sticky=W+E+N+S,      column=1, row=1, padx=2, pady=2)

        if self.rainsensor:
            frmRain = FrameRainSensor(self)
            frmRain.grid(sticky=W+E+N+S,       column=1, row=2, padx=2, pady=2)

        if self.webcam:
            frmWebcam = FrameWebcam(self)
            frmWebcam.grid(sticky=W+E+N+S,     column=1, row=2, padx=1, pady=2)

        if self.console:
            frmConsole = FrameConsole(self)
            frmConsole.grid(sticky=W+E+N+S,    column=0, row=3, padx=1, pady=2,
                            columnspan=2)

    def read_config(self):
        parser = ConfigParser()
        parser.read('config_dynamic.ini')
        self.loglevel = parser.get('hypstar', 'loglevel')
        self.baudrate = parser.getint('hypstar', 'baudrate')
        self.tec_target_temp = parser.get('hypstar', 'swir_tec')
        self.serial_port = parser.get('hypstar', 'hypstar_port')
        self.verbosity = parser.get('general', 'verbosity')


if __name__ == '__main__':
    # TODO : global var for YOCTO api
    gui = Guied()
