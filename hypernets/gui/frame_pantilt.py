#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S, NE, NW, SE, SW, SE, BOTH, DISABLED, END  # noqa
from tkinter import Label, LabelFrame, Spinbox
from tkinter import Tk, Button
from tkinter.ttk import Combobox

from hypernets.scripts.pan_tilt import move_to


class FramePanTilt(LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Pan-Tilt", padx=2, pady=4)
        self.configure_items_pantilt()

    def configure_items_pantilt(self):
        # --------------------------------------------------------------------
        # Objects definitions
        # --------------------------------------------------------------------
        self.pan = Spinbox(self, from_=0, to=360, width=5,
                           format="%.1f", increment=0.1, wrap=True)
        # ---------------------------------------------------------------------
        self.tilt = Spinbox(self, from_=0, to=360, width=5,
                            format="%.1f", increment=0.1, wrap=True)
        # ---------------------------------------------------------------------
        # self.reference = Combobox(self, state="disabled")
        self.reference = Combobox(self)
        self.reference['values'] = ("Absolute", "North", "Sun")
        # ---------------------------------------------------------------------
        movePT = Button(self, text="Move Pan-Tilt", command=self.callback)
        # ---------------------------------------------------------------------
        self.pan.grid(sticky=W,       column=1, row=0)
        self.tilt.grid(sticky=W,      column=1, row=1)
        self.reference.grid(sticky=W, column=1, row=2, pady=4, columnspan=2)
        movePT.grid(sticky=N+S,       column=2, row=0, pady=5, rowspan=2)
        # --------------------------------------------------------------------
        # Some labels :
        # --------------------------------------------------------------------
        for text, col, row, padx, pady, sticky in \
                [("Pan (°) : ",   0, 0, 2, 2, E),
                 ("Tilt (°) : ",  0, 1, 2, 2, E),
                 ("Reference : ", 0, 2, 2, 2, W)]:
            Label(self, text=text)\
                .grid(column=col, row=row, padx=padx, pady=pady, sticky=sticky)
        # ---------------------------------------------------------------------

    def callback(self):
        # See FIXME in frame_pantilt
        move_to(None, float(self.pan.get()), float(self.tilt.get()))


if __name__ == '__main__':
    root = Tk()
    root.title("Set/Get PanTilt position")
    frmPanTilt = FramePanTilt(root)
    frmPanTilt.grid(sticky=N+S+E+W)
    root.mainloop()
