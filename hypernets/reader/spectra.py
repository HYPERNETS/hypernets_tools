
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from hypernets.reader.spectrum import Spectrum
from hypernets.reader.wavelength_to_rgba import make_color_list


def show_interactive_plots(spectra):

    # Next Button
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(spectra.next_spectrum)

    # Previous Button
    axprev = plt.axes([0.12, 0.05, 0.1, 0.075])
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(spectra.prev_spectrum)

    plt.show()


class Spectra(list[Spectrum]):
    def __init__(self, filename, figure=None, axes=None, fancy_mode=True):

        if figure is not None and axes is not None and fancy_mode is True:
            self.clim, self.col = make_color_list()

        self.figure = figure
        self.axes = axes
        self.fancy_mode = fancy_mode

        self.index = 0
        self.cc = None

        # Open the file and create a list of Spectrum
        with open(filename, 'rb') as fd:
            spectra_file = fd.read()

        index = 0
        while index < len(spectra_file):
            current_spectrum = Spectrum(spectra_file[index:], verbose=True)
            self.append(current_spectrum)
            index += current_spectrum.total

        print(f"{len(self)} spectra readed.")

        self.update()

    def next_spectrum(self, event):
        self.index = (self.index + 1) % len(self)
        self.update()

    def prev_spectrum(self, event):
        self.index = (self.index - 1) % len(self)
        self.update()

    def update(self):
        self.current_spectrum = self[self.index]

        if self.axes is not None:
            self.axes.clear()
            x, y = self.scale_wavelength()

            if self.fancy_mode:

                import numpy as np
                extent = (np.min(x), np.max(x), np.min(y), np.max(y))
                X, _ = np.meshgrid(x, y)

                self.axes.imshow(X, clim=self.clim, extent=extent,
                                 cmap=self.col, aspect='auto')

                self.axes.fill_between(x, y, max(y), color='w')

            else:
                self.axes.plot(x, y)

            info = Spectrum.read_spectrum_info(self.current_spectrum.spec_type)
            self.axes.set_title(f"Spectrum {self.index+1}/{len(self)}\n"
                                f"{info[0]} --> {info[1]}")

            self.axes.set_ylabel("Raw Counts")

            if self.cc is not None:
                self.axes.set_xlabel("Wavelength (nm)")

        if self.figure is not None:
            self.figure.canvas.draw()

    def scale_wavelength(self):

        def apply(x, coefs):
            return sum([k * (x**p) for p, k in enumerate(coefs)])

        if self.cc is None:
            try:
                from pickle import load
                with open("config.dump", 'rb') as conf:
                    _, self.cc, _ = load(conf)
                    print(self.cc)

            except Exception as e:
                print(f"Warning : {e}")
                self.fancy_mode = False

        x = range(len(self.current_spectrum.counts))
        y = self.current_spectrum.counts

        s_typ, _ = Spectrum.read_spectrum_info(self.current_spectrum.spec_type)

        if self.cc is not None:
            if s_typ == 'VIS':
                x = [apply(i, list(self.cc.vnir_wavelength_coefficients)) for i in x] # noqa
                y = [i/apply(i, list(self.cc.vnir_lin_coefs)) for i in y]

            elif s_typ == 'SWIR':
                x = [apply(i, list(self.cc.swir_wavelength_coefs)) for i in x]
                # y = [i/apply(i, vnir_lin) for i in y] ?

        return x, y
