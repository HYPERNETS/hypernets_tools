#!/usr/bin/python3
# coding: utf-8
import tkinter
from tkinter import E, W, N, S, HORIZONTAL
from tkinter import Label, LabelFrame, Spinbox, StringVar
from tkinter import Tk, Button
from tkinter.ttk import Combobox, Separator

from tkinter.messagebox import showerror, showinfo

from re import sub

import math
import numpy as np
from PIL import Image, ImageTk

from hypernets.hypstar.handler import HypstarHandler

from hypernets.abstract.request import Request
from hypernets.hypstar.libhypstar.python.data_structs.hardware_info import HypstarSupportedBaudRates
from hypernets.hypstar.libhypstar.python.data_structs.spectrum_raw import RadiometerEntranceType
from hypernets.hypstar.libhypstar.python.data_structs.varia import ValidationModuleLightType
from hypernets.hypstar.libhypstar.python.hypstar_wrapper import HypstarLogLevel

from hypernets.reader.spectrum import Spectrum
from hypernets.reader.spectra import Spectra, show_interactive_plots
import matplotlib.pyplot as plt


class FrameRadiometer(LabelFrame):
    vm_light_source = ValidationModuleLightType.LIGHT_VIS

    def __init__(self, parent):
        super().__init__(parent, relief="groove", labelanchor='nw',
                         text="Radiometer", padx=2, pady=10)

        self.enable_vm_button_text = StringVar()
        self.enable_vm_button_text.set("Turn VM electronics on")
        self.vm_enabled = False
        self.configure_items_radiometer()
        self.configure_items_output()
        self.last_file_path = None
        self.spectra = None
        self.hypstar = None
        self.calibration_coefficients = None

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
        radiometer = Combobox(self, width=20, state="readonly",
                              textvariable=self.radiometer_var[0])
        radiometer['values'] = ("VNIR", "SWIR", "BOTH")
        # --------------------------------------------------------------------
        entrance = Combobox(self, width=20, state="readonly",
                            textvariable=self.radiometer_var[1])
        entrance['values'] = ("Irradiance", "Radiance", "Dark", "Picture")
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
        light_source_cb = Combobox(self, width=20,
                                values=ValidationModuleLightType._member_names_,
                                textvariable = self.vm_light_source)
        # --------------------------------------------------------------------
        self.vm_current = tkinter.DoubleVar(value=1.0)
        light_source_current_sb = Spinbox(self, from_=0.05, to=3.5, increment=0.01,
                                          width=10, textvariable=self.vm_current)
        # --------------------------------------------------------------------
        run = Button(self, text="Acquisition", command=self.general_callback)
        # --------------------------------------------------------------------
        # init_ins = Button(self, text="Hypstar Init",
        #                   command=self.hypstar_instanciatiation)
        # --------------------------------------------------------------------
        get_env_b = Button(self, text="Get Environmental Log",
                           command=self.get_instrument_env_log)
        # --------------------------------------------------------------------
        get_hw_b = Button(self, text="Get Hardware Infos",
                          command=self.get_instrument_hw_info)

        # --------------------------------------------------------------------
        set_tec_b = Button(self, text="Set Thermal Control",
                           command=self.set_swir_temperature)

        unset_tec_b = Button(self, text="Unset Thermal Control",
                             command=self.unset_swir_temperature)

        enable_vm_b = Button(self, textvariable=self.enable_vm_button_text, command=self.enable_vm)

        capture_vm_b = Button(self, text="Measure VM", command=self.measure_vm)

        # --------------------------------------------------------------------
        # Init Values
        # --------------------------------------------------------------------
        radiometer.current(0)
        entrance.current(0)
        IT_vnir.current(0)
        IT_swir.current(0)
        IT_total.current(0)
        resolution.current(0)
        light_source_cb.current(ValidationModuleLightType.LIGHT_VIS.value)
        # --------------------------------------------------------------------
        radiometer.grid(sticky=E,        column=1, row=0)
        entrance.grid(sticky=E,          column=1, row=1)
        IT_vnir.grid(sticky=E,           column=1, row=2)
        IT_swir.grid(sticky=E,           column=1, row=3)
        repeat.grid(sticky=E,            column=1, row=4)
        IT_total.grid(sticky=E,          column=1, row=5)
        resolution.grid(sticky=E,        column=1, row=6)
        light_source_cb.grid(sticky=E,   column=1, row=7)
        light_source_current_sb.grid(sticky=E,column=1, row=8)
        run.grid(sticky=W+E+S+N,         column=1, row=9, padx=2, pady=2)
        # init_ins.grid(sticky=W+E+S+N,    column=0, row=7, padx=2, pady=2)
        get_env_b.grid(sticky=W+E+S+N,   column=0, row=10, padx=2, pady=2)
        get_hw_b.grid(sticky=W+E+S+N,    column=1, row=10, padx=2, pady=2)
        set_tec_b.grid(sticky=W+E+S+N,   column=0, row=11, padx=2, pady=2)
        unset_tec_b.grid(sticky=W+E+S+N, column=1, row=11, padx=2, pady=2)
        enable_vm_b.grid(sticky=W+E+S+N, column=0, row=12, padx=2, pady=2)
        capture_vm_b.grid(sticky=W+E+S+N, column=1, row=12, padx=2, pady=2)

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
                 ("VM Light source : ",         0, 7, 2, 2, E),
                 ("VM Current setting : ",      0, 8, 2, 2, E),
                 ("ms",                         3, 2, 2, 2, W),
                 ("ms",                         3, 3, 2, 2, W),
                 ("ms",                         3, 5, 2, 2, W)]:

            Label(self, text=text)\
                .grid(column=col, row=row, padx=padx, pady=pady, sticky=sticky)
        # --------------------------------------------------------------------

    def check_if_hypstar_exists(self):
        if self.hypstar is None:
            try:
                self.hypstar = HypstarHandler(instrument_port=self.master.serial_port, 
                                              instrument_baudrate=self.master.baudrate, 
                                              expect_boot_packet=False, 
                                              instrument_loglevel=int(HypstarLogLevel[self.master.loglevel]))
                self.hypstar.set_baud_rate(HypstarSupportedBaudRates(self.master.baudrate))
                self.calibration_coefficients = self.hypstar.get_calibration_coeficients_basic()

            except Exception as e:
                showerror("Error", str(e))
                return False
        return True

    def general_callback(self):

        radiometer, entrance, it_vnir, it_swir, count, total, reso = \
            [v.get() for v in self.radiometer_var]

        radiometer, entrance = radiometer.lower(), entrance.lower()[:3]
        it_vnir, it_swir, count = int(it_vnir), int(it_swir), int(count)
        measurement = radiometer, entrance, it_vnir, it_swir
        request = Request.from_params(count, *measurement)

        if not self.check_if_hypstar_exists():
            return

        try:
            self.last_file_path = self.hypstar.take_request(request, gui=True)
            self.make_output()

            self.master.option_add('*Dialog.msg.width', 60)
            self.master.option_add('*Dialog.msg.wrapLength', 800)
            showinfo("End Acquisition", f"Saved to : {self.last_file_path}")
            self.option_clear()
            self.master.option_clear()

        except Exception as e:
            showerror("Error", str(e))

    def configure_items_output(self):
        output_frame = LabelFrame(self, text="Output")
        output_frame.grid(sticky=W+E+S+N,  column=0, row=13,  columnspan=2)

        separator = Separator(output_frame, orient=HORIZONTAL)

        show_graph = Button(output_frame, text="Show plot",
                            command=self.show_plot)

        prev_spec = Button(output_frame, text="Prev Spectrum",
                           command=self.prev_spec)

        next_spec = Button(output_frame, text="Next Spectrum",
                           command=self.next_spec)

        # ---------------------------------------------------------------------
        # Labels
        for text, col, row, padx, pady, sticky in \
                [("Spectrum # : ",            0, 0, 2, 2, E),
                 ("Length : ",                0, 1, 2, 2, E),
                 ("Type : ",                  0, 2, 2, 2, E),
                 ("Exposure : ",              0, 3, 2, 2, E),
                 ("Temperature : ",           0, 4, 2, 2, E),
                 ("Acceleration : \n (m/s²)", 0, 5, 2, 2, E),
                 ("Timestamp : ",             0, 6, 2, 2, E)]:

            Label(output_frame, text=text)\
                .grid(column=col, row=row, padx=padx, pady=pady, sticky=sticky)
        # ---------------------------------------------------------------------
        # Values
        self.str_number = StringVar(self)
        self.str_lenght = StringVar(self)
        self.str_type = StringVar(self)
        self.str_expo = StringVar(self)
        self.str_temperature = StringVar(self)
        self.str_accel = StringVar(self)
        self.str_timestamp = StringVar(self)

        for text, col, row, padx, pady, sticky in \
                [(self.str_number,      1, 0, 2, 2, W),
                 (self.str_lenght,      1, 1, 2, 2, W),
                 (self.str_type,        1, 2, 2, 2, W),
                 (self.str_expo,        1, 3, 2, 2, W),
                 (self.str_temperature, 1, 4, 2, 2, W),
                 (self.str_accel,       1, 5, 2, 2, W),
                 (self.str_timestamp,   1, 6, 2, 2, W)]:

            Label(output_frame, textvariable=text)\
                .grid(column=col, row=row, padx=padx, pady=pady, sticky=sticky)

        # ---------------------------------------------------------------------
        separator.grid(sticky=N,  column=0, row=7,  columnspan=4)
        show_graph.grid(sticky=W, column=0, row=10, columnspan=2)
        prev_spec.grid(sticky=W,  column=1, row=10, columnspan=1)
        next_spec.grid(sticky=W,  column=2, row=10, columnspan=1)


    def prev_spec(self):
        if self.spectra is None:
            showerror("Error", "Please take an acquisition")
            return

        # plot window has been shown and closed, re-init
        if self.spectra.shown is True:
            self.make_output()

        self.spectra.prev_spectrum(None)
        self.update_output()


    def next_spec(self):
        if self.spectra is None:
            showerror("Error", "Please take an acquisition")
            return

        # plot window has been shown and closed, re-init
        if self.spectra.shown is True:
            self.make_output()

        self.spectra.next_spectrum(None)
        self.update_output()


    def show_plot(self, nofile=False):
        if not nofile and self.last_file_path is None or self.spectra is None:
            showerror("Error", "Please take an acquisition")
            return
        
        # plot window has been shown and closed, re-init
        if self.spectra.shown is True:
            self.make_output()

        show_interactive_plots(self.spectra)


    def make_output(self, spec=None):
        if self.last_file_path is None and spec is None:
            return

        if spec is None:
            # image processing separately
            if self.last_file_path.endswith('.jpg'):
                img = ImageTk.PhotoImage(Image.open(self.last_file_path).reduce(3))
                win = tkinter.Toplevel()
                win.wm_title("Image")
                l = tkinter.Label(win, image=img)
                # need to set image once again (PILTk bug? IDK)
                l.image = img
                l.pack()
                return

            self.figure, self.axes = plt.subplots()
            plt.subplots_adjust(bottom=0.2)
            self.spectra = Spectra(self.last_file_path, figure=self.figure,
                                   axes=self.axes, cc=self.calibration_coefficients)
            self.update_output()
        else:
            self.figure, self.axes = plt.subplots()
            plt.subplots_adjust(bottom=0.2)
            self.spectra = Spectra(None, figure=self.figure,
                                   axes=self.axes, cc=self.calibration_coefficients, spectrum=spec)
            self.update_output(nofile=True)

    def update_output(self, nofile=False):
        if not nofile and self.last_file_path is None:
            showerror("Error", "Please take an acquisition")
            return

        current_spectrum = self.spectra.current_spectrum

        self.str_number.set(f"{self.spectra.index + 1}/{len(self.spectra)}")

        self.str_lenght.set(f"{current_spectrum.total} bytes"
                            f" ; {current_spectrum.pixel_count} pixels")

        # To m.s^-2
        def to_mss(x):
            return x * 19.6 / 32768.0

        spec_type = Spectrum.read_spectrum_info(current_spectrum.spec_type)
        self.str_type.set(f"{spec_type[0]} -> {spec_type[1]}")
        self.str_expo.set(f"{current_spectrum.exposure_time} ms")
        self.str_temperature.set(f"{current_spectrum.temperature}\u00b0C")
        self.str_accel.set(
            f"X: {to_mss(current_spectrum.mean_X):.2f} \u00b1 {to_mss(current_spectrum.std_Z):.2f}\n" # noqa
            f"Y: {to_mss(current_spectrum.mean_Y):.2f} \u00b1 {to_mss(current_spectrum.std_Y):.2f}\n" # noqa
            f"Z: {to_mss(current_spectrum.mean_Z):.2f} \u00b1 {to_mss(current_spectrum.std_Z):.2f}") # noqa

        self.str_timestamp.set(f"{current_spectrum.timestamp} ms")

    def get_instrument_hw_info(self):
        if not self.check_if_hypstar_exists():
            return
        self.hypstar.get_hw_info()
        showinfo("Hardware Infos", str(self.hypstar.hw_info))

    def get_instrument_env_log(self):
        if not self.check_if_hypstar_exists():
            return
        output = str(self.hypstar.get_env_log())
        if isinstance(output, Exception):
            showerror("Error", str(output))

        self.option_add('*Dialog.msg.font', 'Helvetica 10')
        self.master.option_add('*Dialog.msg.width', 90)
        self.master.option_add('*Dialog.msg.wrapLength', 800)
        output = sub(r"\t+", " ", output)
        showinfo("Environmental Logs", output)
        self.option_clear()
        self.master.option_clear()


    def set_swir_temperature(self):
        TEC = 0  # TODO : tunable from config / gui ?
        if not self.check_if_hypstar_exists():
            return

        print(f"Stabilising SWIR sensor temperature to {TEC} 'C...")
        try:
            self.hypstar.set_SWIR_module_temperature(TEC)
        except Exception as e:
            showerror("Error", str(e))
            return

        showinfo("Thermal Control3", f"SWIR temperature set to {TEC} 'C")


    def unset_swir_temperature(self):
        if not self.check_if_hypstar_exists():
            return

        try:
            self.hypstar.shutdown_SWIR_module_thermal_control()
        except Exception as e:
            showerror("Error", str(e))
            return

        showinfo("Thermal Control", "SWIR Thermal Control is disabled")


    def enable_vm(self):
        if not self.check_if_hypstar_exists():
            return

        self.vm_enabled = not self.vm_enabled
        if self.vm_enabled:
            self.enable_vm_button_text.set("Turn VM electronics off")
            self.hypstar.VM_enable(True)
        else:
            self.enable_vm_button_text.set("Turn VM electronics on")
            self.hypstar.VM_enable(False)

        output = self.hypstar.VM_enable(self.vm_enabled)
        if isinstance(output, Exception):
            showerror("Error", str(output))
        pass


    def measure_vm(self):
        if not self.check_if_hypstar_exists():
            return

        it = int(self.radiometer_var[2].get() if self.vm_light_source.value < 2 else self.radiometer_var[3].get())

        spec = self.hypstar.VM_measure(RadiometerEntranceType[self.radiometer_var[1].get().upper()].value, 
                self.vm_light_source.value, it, self.vm_current.get())

        spec = spec.getBytes()

        # turn off VM after measuring
        self.enable_vm_button_text.set("Turn VM electronics on")
        self.hypstar.VM_enable(False)
        self.vm_enabled = False

        self.make_output(spec=spec)
        self.show_plot(nofile=True)


    def read_cal(self):
        pass


    def __del__(self):
        if self.hypstar is not None:
            del self.hypstar


if __name__ == '__main__':
    root = Tk()
    root.title("Instrument Acquisisition")
    frmRadiometer = FrameRadiometer(root)
    frmRadiometer.grid(sticky=W+E+N+S)
    root.mainloop()
