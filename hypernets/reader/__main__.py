
from hypernets.reader.spectrum import Spectrum
from hypernets.reader.specta import Spectra

import matplotlib.pyplot as plt
from matplotlib.widgets import Button




filename = "01_001_0090_2_0180_128_08_0000_99_0000.spe"

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
spectrum = Spectra(filename).current_spectrum
line, = plt.plot(range(len(spectrum.counts)), spectrum.counts)

callback = Spectra(filename, line)

# Next Button
axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
bnext = Button(axnext, 'Next')
bnext.on_clicked(callback.next_spectrum)

# Previous Button
axprev = plt.axes([0.15, 0.05, 0.1, 0.075])
bprev = Button(axprev, 'Previous')
bprev.on_clicked(callback.prev_spectrum)

plt.show()

if __name__ == '__main__':
    print("hool"):q

