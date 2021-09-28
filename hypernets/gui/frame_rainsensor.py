#!/usr/bin/python3
# coding: utf-8

from tkinter import E, W, N, S, NE, NW, SE, SW, SE, BOTH, DISABLED, END  # noqa
from tkinter import LabelFrame
from tkinter import Tk, Button
from tkinter.messagebox import showinfo

from hypernets.rain_sensor.rain_sensor_python import RainSensor


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
        rain_sensor = RainSensor()
        v = rain_sensor.read_value()
        str_val = {0: "no rain", 1: "rain"}[v]
        showinfo("Value", f"Readed value is : {str_val}.")


if __name__ == '__main__':
    root = Tk()
    root.geometry("400x70")
    root.title("Read the Rain Sensor Value")
    frmRainSensor = FrameRainSensor(root)
    frmRainSensor.grid(sticky=N+S+E+W)
    root.mainloop()
