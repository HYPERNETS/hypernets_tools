#!/usr/bin/python3
# coding: utf-8


from tkinter import E, W, N, S
from tkinter import Label, LabelFrame, Spinbox, StringVar
from tkinter import Tk, Button
from tkinter.ttk import Combobox

from tkinter.messagebox import showerror

from hypernets.scripts.call_radiometer import take_spectra, take_picture
from datetime import datetime

from os import path


class FrameRadiometer(LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Radiometer", padx=2, pady=10)

        self.configure_items_radiometer()
        self.configure_items_output()

    def configure_items_radiometer(self):
        self.radiometer_var = [StringVar(self) for _ in range(7)]
        # --------------------------------------------------------------------
        range_IT = tuple([0]+[pow(2, i) for i in range(16)])
        # --------------------------------------------------------------------
        range_IMG = ("160 x 120, QQVGA",
                     "176 x 144, QCIF",
                     "320 x 240, QVGA",
                     "400 x 240, WQVGA",
                     "352 x 288, CIF",
                     "640 x 480, VGA",
                     "800 x 600, WVGA",
                     "1024 x 768, XGA",
                     "1280 x 720, 720p",
                     "1280 x 960, SXGA",
                     "1600 x 1200, UXGA",
                     "1920 x 1080, 1080p",
                     "1920 x 1200, WUXGA",
                     "2048 x 1536, QXGA",
                     "2592 x 1944, 5MP")

        range_IMG = ("2592 x 1944, 5MP", '')
        # --------------------------------------------------------------------
        # Objects definitions
        # --------------------------------------------------------------------
        mode = Combobox(self, width=20, state="readonly",
                        textvariable=self.radiometer_var[0])
        mode['values'] = ("VNIR", "SWIR", "BOTH")
        # --------------------------------------------------------------------
        action = Combobox(self, width=20, state="readonly",
                          textvariable=self.radiometer_var[1])
        action['values'] = ("Irradiance", "Radiance", "Dark", "Picture")
        # --------------------------------------------------------------------
        IT_vnir = Combobox(self, width=10, values=range_IT, state="readonly",
                           textvariable=self.radiometer_var[2])
        # --------------------------------------------------------------------
        IT_swir = Combobox(self, width=10, values=range_IT, state="readonly",
                           textvariable=self.radiometer_var[3])
        # --------------------------------------------------------------------
        IT_total = Combobox(self, width=10, values=range_IT, state="disabled",
                            textvariable=self.radiometer_var[5])
        # --------------------------------------------------------------------
        repeat = Spinbox(self, from_=1, to=65535, width=10,
                         textvariable=self.radiometer_var[4])
        # --------------------------------------------------------------------
        resolution = Combobox(self, width=20, values=range_IMG,
                              textvariable=self.radiometer_var[6],
                              state="disabled")  # state="readonly")
        # --------------------------------------------------------------------
        run = Button(self, text="Acquisition", command=self.general_callback)
        # --------------------------------------------------------------------
        # Init Values
        # --------------------------------------------------------------------
        mode.current(0)
        action.current(0)
        IT_vnir.current(0)
        IT_swir.current(0)
        IT_total.current(0)
        resolution.current(0)
        # --------------------------------------------------------------------
        mode.grid(sticky=E,       column=1, row=0)
        action.grid(sticky=E,     column=1, row=1)
        IT_vnir.grid(sticky=E,    column=1, row=2)
        IT_swir.grid(sticky=E,    column=1, row=3)
        repeat.grid(sticky=E,     column=1, row=4)
        IT_total.grid(sticky=E,   column=1, row=5)
        resolution.grid(sticky=E, column=1, row=6)
        run.grid(sticky=W+E+S+N,  column=0, row=7,  columnspan=2,
                 padx=2, pady=2)
        # --------------------------------------------------------------------
        # Some labels :
        # --------------------------------------------------------------------
        for text, col, row, padx, pady, sticky in \
                [("Radiometer : ",              0, 0, 2, 2, E),
                 ("Entrance : ",                0, 1, 2, 2, E),
                 ("Integration time (VNIR) : ", 0, 2, 2, 2, E),
                 ("Integration time (SWIR): ",  0, 3, 2, 2, E),
                 ("Number of captures : ",      0, 4, 2, 2, E),
                 ("Total measurement time : ",  0, 5, 2, 2, E),
                 ("Image Resolution : ",        0, 6, 2, 2, E),
                 ("ms",                         3, 2, 2, 2, W),
                 ("ms",                         3, 3, 2, 2, W),
                 ("ms",                         3, 5, 2, 2, W)]:

            Label(self, text=text)\
                .grid(column=col, row=row, padx=padx, pady=pady, sticky=sticky)
        # --------------------------------------------------------------------

    def general_callback(self):
        mode, action, vnir, swir, cap_count, total, reso = \
            [v.get() for v in self.radiometer_var]

        print(mode, action, vnir, swir, cap_count, total, reso)

        output_dir = "DATA"
        output_name = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

        if action == "Picture":
            output_name += ".jpg"
            take_picture(path.join(output_dir, output_name))

        elif mode in ['VNIR', 'SWIR', 'BOTH'] and \
                action in ['Irradiance', 'Radiance', 'Dark']:

            output_name += f"_{mode}"
            output_name += f"_{action[:3]}"
            output_name += "_{:0=5d}".format(int(vnir))
            output_name += "_{:0=5d}".format(int(swir))
            output_name += "_{:0=2d}".format(int(cap_count))
            output_name += ".spe"

            # Translation into "sequence file syntax" for radiometer call
            vnir, swir, cap_count = int(vnir), int(swir), int(cap_count)
            mode = {"VNIR": "vis", "SWIR": "swi", "BOTH": "bot"}[mode]
            action = {"Radiance": "rad", "Irradiance": "irr",
                      "Dark": "bla"}[action]

            int_times = take_spectra(path.join(output_dir, output_name),
                                     mode, action, vnir, swir, cap_count)

            if isinstance(int_times, Exception):
                showerror("Error", str(int_times))

            elif isinstance(int_times, tuple):
                print(f"Integration Times : VNIR : {int_times[0]} ms")
                print(f"                  : SWIR : {int_times[1]} ms")

    def configure_items_output(self):

        output_frame = LabelFrame(self, text="Output")
        output_frame.grid(sticky=W+E+S+N,  column=0, row=8,  columnspan=2)
        show_graph = Button(output_frame, text="Show graph !")
        # ---------------------------------------------------------------------
        show_graph.grid(sticky=W, column=1, row=1)
        # ---------------------------------------------------------------------


if __name__ == '__main__':
    root = Tk()
    root.title("Instrument Acquisisition")
    frmRadiometer = FrameRadiometer(root)
    frmRadiometer.grid(sticky=W+E+N+S)
    root.mainloop()
