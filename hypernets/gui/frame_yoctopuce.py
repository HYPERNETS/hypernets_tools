#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S
from tkinter import LabelFrame
from tkinter import Tk, Button

from hypernets.scripts.relay_command import get_state_relay, set_state_relay


class FrameYoctopuce(LabelFrame):
    def __init__(self, parent):

        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Yocto-Pictor", padx=2, pady=4)

        self.configure_items_yocto()
        self.relays_states = [None for _ in range(6)]

    def configure_items_yocto(self):
        # --------------------------------------------------------------------
        # Objects definitions
        # ---------------------------------------------------------------------
        connection = Button(self, text="Connection", command=self.connection)
        # ---------------------------------------------------------------------
        frm_relays = LabelFrame(self, relief="groove", labelanchor='nw',
                                text="Relays")

        self.relays = [Button(frm_relays, text="N°" + str(i+1),
                              command=lambda x=i+1: self.callback(x))
                       for i in range(6)]

        for i, relay in enumerate(self.relays):
            relay.grid(column=i, row=0)
        # ---------------------------------------------------------------------

        connection.grid(sticky=W, column=0, row=0)
        frm_relays.grid(sticky=W, column=0, row=1)

    def callback(self, i):
        if self.relays_states[i-1] is True:
            set_state_relay(i, "off")

        elif self.relays_states[i-1] is False:
            set_state_relay(i, "on")

        self.connection()

    def connection(self):
        states_relay = get_state_relay(-1)
        for id_relay, state in enumerate(states_relay):
            if state[1]:
                self.relays[id_relay].configure(bg="green")
                self.relays_states[id_relay] = True
            else:
                self.relays[id_relay].configure(bg="red")
                self.relays_states[id_relay] = False


if __name__ == '__main__':
    root = Tk()
    root.title("Yoctopuce Control")
    frmYocto = FrameYoctopuce(root)
    frmYocto.grid(sticky=N+S+W+E)
    root.mainloop()
