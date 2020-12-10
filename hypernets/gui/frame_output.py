#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S  # noqa
from tkinter import LabelFrame
from tkinter import Tk, Button


class FrameOutput(LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Output", padx=2, pady=4)

        self.configure_items_webcam()

    def configure_items_webcam(self):
        # --------------------------------------------------------------------
        # Objects definitions
        # ---------------------------------------------------------------------
        show_graph = Button(self, text="Show graph !")
        # ---------------------------------------------------------------------
        show_graph.grid(sticky=W, column=1, row=1)
        # ---------------------------------------------------------------------


if __name__ == '__main__':
    root = Tk()
    root.title("Output")
    frmYocto = FrameOutput(root)
    frmYocto.grid(sticky=N+S+W+E)
    root.mainloop()
