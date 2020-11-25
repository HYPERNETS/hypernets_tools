from hypernets.reader.spectrum import Spectrum


class Spectra(object):
    def __init__(self, filename, line=None):

        self.index = 0
        self.offset = 0
        self.line = line

        with open(filename, 'rb') as fd:
            self.data = fd.read()

        self.update()

    def next_spectrum(self, event):
        # TODO : boundary
        self.index += 1
        self.offset += self.current_spectrum.total
        self.update()

    def prev_spectrum(self, event):
        # TODO : ensure positivity
        self.index -= 1
        self.offset -= self.current_spectrum.total  # different when spec BOTH
        self.update()

    def update(self, plt):
        self.current_spectrum = Spectrum(self.data[self.offset:])  # not optim
        if self.line is not None:
            self.line.set_ydata(self.current_spectrum.counts)
            plt.draw()
