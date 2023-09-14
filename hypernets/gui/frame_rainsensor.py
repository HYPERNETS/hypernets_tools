#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S, NE, NW, SE, SW, SE, BOTH, DISABLED, END  # noqa
from tkinter import LabelFrame
from tkinter import Tk, Button
from tkinter.messagebox import showinfo, showerror

from hypernets.rain_sensor import RainSensor


class FrameRainSensor(LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Rain Sensor", padx=2, pady=4)
        self.configure_items_pantilt()

    def configure_items_pantilt(self):
        # --------------------------------------------------------------------
        # Objects definitions
        # --------------------------------------------------------------------
        readValue = Button(self, text="Read Value", command=self.callback)
        # ---------------------------------------------------------------------
        readValue.grid(pady=5)

    def callback(self):
        try:
            rain_sensor = RainSensor()
            v = rain_sensor.read_value()
            str_val = {0: "no rain", 1: "rain"}[v]
            showinfo("Value", f"Read value : {str_val}.")

        except Exception as e:
            showerror("Error", str(e))


if __name__ == '__main__':
    root = Tk()
    root.geometry("400x70")
    root.title("Read the Rain Sensor Value")
    frmRainSensor = FrameRainSensor(root)
    frmRainSensor.grid(sticky=N+S+E+W)
    root.mainloop()
