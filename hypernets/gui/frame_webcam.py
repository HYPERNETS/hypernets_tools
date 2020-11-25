#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S  # noqa
from tkinter import LabelFrame
from tkinter import Tk, Button


class FrameWebcam(LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Webcams", padx=2, pady=4)

        self.configure_items_webcam()

    def configure_items_webcam(self):
        # --------------------------------------------------------------------
        # Objects definitions
        # ---------------------------------------------------------------------
        webcam_land_ping = Button(self, text="Webcam site ping")
        webcam_inst_ping = Button(self, text="Webcam instrument ping")
        webcam_land_test = Button(self, text="Webcam site test")
        webcam_inst_test = Button(self, text="Webcam instrument test")
        # ---------------------------------------------------------------------
        webcam_land_ping.grid(sticky=W, column=0, row=0)
        webcam_inst_ping.grid(sticky=W, column=1, row=0)
        webcam_land_test.grid(sticky=W, column=0, row=1)
        webcam_inst_test.grid(sticky=W, column=1, row=1)
        # ---------------------------------------------------------------------


if __name__ == '__main__':
    root = Tk()
    root.title("Webcam Test")
    frmYocto = FrameWebcam(root)
    frmYocto.grid(sticky=N+S+W+E)
    root.mainloop()
