#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S, NE, NW, SE, SW, SE, BOTH, DISABLED, END  # noqa
from tkinter import PhotoImage, Label
from tkinter import Tk

from hypernets.gui.frame_radiometer import FrameRadiometer
from hypernets.gui.frame_pantilt import FramePanTilt
from hypernets.gui.frame_yoctopuce import FrameYoctopuce
from hypernets.gui.frame_webcam import FrameWebcam
from hypernets.gui.frame_console import FrameConsole

from importlib import resources as get_resources
from hypernets import resources


class Guied(Tk):
    def __init__(self):
        super().__init__()

        self.radiometer = True
        self.pantilt = True
        self.yoctopuce = True
        self.output = True

        self.webcam = False
        self.console = False

        self.create_logo()
        self.configure_frames()
        self.configure_gui()
        self.mainloop()

    def configure_gui(self):
        self.title("Guied - Hypernets GUI")
        # self.geometry('700x550')
        # self.resizable(0, 0)

    def create_logo(self):
        logo_hypernets = get_resources.read_binary(resources, "logo.png")
        self.img_hyp = PhotoImage(data=logo_hypernets)
        logo_lbl = Label(self, image=self.img_hyp)
        logo_lbl.grid(column=0, row=0, columnspan=2)

    def configure_frames(self):
        if self.radiometer:
            frmRadiometer = FrameRadiometer(self)
            frmRadiometer.grid(sticky=W+E+N+S, column=0, row=1, padx=2, pady=2,
                               rowspan=2)

        if self.pantilt:
            frmPanTilt = FramePanTilt(self)
            frmPanTilt.grid(sticky=W+E+N+S,    column=1, row=2, padx=2, pady=2)

        if self.yoctopuce:
            frmYocto = FrameYoctopuce(self)
            frmYocto.grid(sticky=W+E+N+S,      column=1, row=1, padx=2, pady=2)

        if self.webcam:
            frmWebcam = FrameWebcam(self)
            frmWebcam.grid(sticky=W+E+N+S,     column=1, row=2, padx=1, pady=2)

        if self.console:
            frmConsole = FrameConsole(self)
            frmConsole.grid(sticky=W+E+N+S,    column=0, row=3, padx=1, pady=2,
                            columnspan=2)


if __name__ == '__main__':
    # TODO : global var for YOCTO api
    gui = Guied()
