from hypernets.reader.spectrum import Spectrum  # noqa
from hypernets.reader.spectra import Spectra

import matplotlib.pyplot as plt
from matplotlib.widgets import Button


if __name__ == '__main__':

    filename = "DATA/20201126T161358_BOTH_Irr_00000_00000_01.spe"
    # filename = "DATA/20201126T163617_SWIR_Irr_00000_00000_01.spe"
    filename = "DATA/20201130T103936_BOTH_Dar_00000_00000_01.spe"

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    # spectrum = Spectra(filename).current_spectrum
    # line, = plt.plot(range(len(spectrum.counts)), spectrum.counts)

    callback = Spectra(filename, line=None, plt=plt)

    # Next Button
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(callback.next_spectrum)

    # Previous Button
    axprev = plt.axes([0.15, 0.05, 0.1, 0.075])
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(callback.prev_spectrum)

    plt.show()
