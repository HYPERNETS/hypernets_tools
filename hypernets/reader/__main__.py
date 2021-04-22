from hypernets.reader.spectrum import Spectrum  # noqa
from hypernets.reader.spectra import Spectra

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from argparse import ArgumentParser
from struct import unpack



if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument("-f", "--filename", type=str, required=True,
                        help="Select Spectra file")

    args = parser.parse_args()

    spectra = Spectra(args.filename)

    spectrum = spectra.current_spectrum

    figure, axes = plt.subplots()
    plt.subplots_adjust(bottom=0.2)

    callback = Spectra(args.filename, figure=figure, axes=axes)

    # Next Button
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(callback.next_spectrum)

    # Previous Button
    axprev = plt.axes([0.12, 0.05, 0.1, 0.075])
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(callback.prev_spectrum)

    plt.show()
