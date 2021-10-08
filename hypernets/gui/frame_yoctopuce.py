#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S
from tkinter import LabelFrame
from tkinter import Tk, Button, Label, StringVar

from hypernets.yocto.relay import get_state_relay, set_state_relay

from hypernets.yocto.meteo import get_meteo
from hypernets.yocto.gps import get_gps


class FrameYoctopuce(LabelFrame):
    def __init__(self, parent):

        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Yocto-Pictor", padx=2, pady=4)

        self.relays_states = [None for _ in range(6)]

        self.meteo_data = StringVar()
        self.gps_data = StringVar()
        self.configure_items_yocto()

    def configure_items_yocto(self):
        # --------------------------------------------------------------------
        # Objects definitions
        # ---------------------------------------------------------------------
        def _connection():
            self.connection()
            self.update_meteo()
            self.update_gps()

        connection = Button(self, text="Connection", command=_connection)
        # ---------------------------------------------------------------------
        frm_relays = LabelFrame(self, relief="groove", labelanchor='nw',
                                text="Relays")

        self.relays = [Button(frm_relays, text="N°" + str(i+1),
                              command=lambda x=i+1: self.callback(x))
                       for i in range(6)]

        for i, relay in enumerate(self.relays):
            relay.grid(column=i, row=1)
        # ---------------------------------------------------------------------
        frm_meteo = LabelFrame(self, relief="groove", labelanchor='nw',
                               text="Meteo")

        update_meteo = Button(frm_meteo, text="update",
                              command=self.update_meteo)

        lbl_meteo = Label(frm_meteo, textvariable=self.meteo_data)

        update_meteo.grid(column=0, row=0)
        lbl_meteo.grid(column=1, row=0, padx=8)
        # ---------------------------------------------------------------------
        frm_gps = LabelFrame(self, relief="groove", labelanchor='nw',
                             text="GPS")
        update_gps = Button(frm_gps, text="update", command=self.update_gps)
        lbl_gps = Label(frm_gps, textvariable=self.gps_data)
        update_gps.grid(column=0, row=0)
        lbl_gps.grid(column=1, row=0, padx=8)
        # ---------------------------------------------------------------------
        lbl_webpage = Label(self, text="http://10.42.0.X")
        # ---------------------------------------------------------------------
        connection.grid(column=0, row=0)
        frm_relays.grid(sticky=W, column=0, row=1)
        frm_meteo.grid(sticky=W, column=0, row=2)
        frm_gps.grid(sticky=W, column=0, row=3)
        lbl_webpage.grid(sticky=W, column=0, row=4)

    def callback(self, i):
        if self.relays_states[i-1] is True:
            set_state_relay([i], "off")

        elif self.relays_states[i-1] is False:
            set_state_relay([i], "on")

        self.connection()

    def connection(self):
        """color update"""
        states_relay = get_state_relay(-1)
        for id_relay, state in enumerate(states_relay):
            if state:
                self.relays[id_relay].configure(bg="green")
                self.relays_states[id_relay] = True
            else:
                self.relays[id_relay].configure(bg="red")
                self.relays_states[id_relay] = False

    def update_meteo(self):
        meteo_data = get_meteo()
        meteo_data = "   ".join([str(val) + unit for val, unit in meteo_data])
        self.meteo_data.set(meteo_data)

    def update_gps(self):
        gps_data = get_gps(return_float=False)
        self.gps_data.set(gps_data)


if __name__ == '__main__':
    root = Tk()
    root.title("Yoctopuce Control")
    frmYocto = FrameYoctopuce(root)
    frmYocto.grid(sticky=N+S+W+E)
    root.mainloop()
