
from argparse import ArgumentParser
from hypernets.reader.spectra import Spectra, show_interactive_plots

import matplotlib.pyplot as plt


if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument("-f", "--filename", type=str, required=True,
                        help="Select Spectra file")

    # parser.add_argument("-d", "--display", type=bool, required=False,
    #                     help="Display Interactive Plots", default=True)

    args = parser.parse_args()

    figure, axes = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    spectra = Spectra(args.filename, figure=figure, axes=axes)
    show_interactive_plots(spectra)
