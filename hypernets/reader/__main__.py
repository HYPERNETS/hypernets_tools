
from argparse import ArgumentParser
from hypernets.reader.spectra import Spectra, show_interactive_plots

import matplotlib.pyplot as plt


if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument("-f", "--filename", type=str, required=True,
                        help="Select Spectra file")

    parser.add_argument("-n", "--no-display", required=False, default=False,
                        action='store_true',
                        help="Don't Display Interactive Plots")

    args = parser.parse_args()

    if args.no_display is False:
        figure, axes = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        spectra = Spectra(args.filename, figure=figure, axes=axes)
        show_interactive_plots(spectra)

    else:
        spectra = Spectra(args.filename)
