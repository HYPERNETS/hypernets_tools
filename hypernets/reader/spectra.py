from hypernets.reader.spectrum import Spectrum
# import matplotlib.pyplot as plt
from matplotlib.widgets import Button



def show_interactive_plots(spectra, plt):

    # Next Button
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(spectra.next_spectrum)

    # Previous Button
    axprev = plt.axes([0.12, 0.05, 0.1, 0.075])
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(spectra.prev_spectrum)

    plt.show()


class Spectra(object):
    def __init__(self, filename, figure=None, axes=None):

        self.figure = figure
        self.axes = axes

        self.index = 0
        self.spectra_list = list()

        # Open the file and create a list of Spectrum
        with open(filename, 'rb') as fd:
            spectra_file = fd.read()

        index = 0 
        while index < len(spectra_file):
            current_spectrum = Spectrum(spectra_file[index:])
            self.spectra_list.append(current_spectrum)
            index += current_spectrum.total

        print(f"{len(self.spectra_list)} spectra readed.")

        self.update()

    def next_spectrum(self, event):
        self.index = (self.index + 1) % len(self.spectra_list)
        self.update()

    def prev_spectrum(self, event):
        self.index = (self.index - 1) % len(self.spectra_list)
        self.update()

    def update(self):
        self.current_spectrum = self.spectra_list[self.index]
        print(self.current_spectrum)

        if self.axes is not None:
            self.axes.clear()
            self.axes.plot(range(len(self.current_spectrum.counts)), 
                           self.current_spectrum.counts)


            spec_info = Spectrum.read_spectrum_info(self.current_spectrum.spec_type)

            self.axes.set_title(f"Spectrum {self.index+1}/{len(self.spectra_list)}\n"
                                f"{spec_info[0]} --> {spec_info[1]}")

            # self.axes.set_xlabel("")
            self.axes.set_ylabel("Raw Counts")

        if self.figure is not None:
            self.figure.canvas.draw()
