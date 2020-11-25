# from shutil import move

from datetime import datetime
from struct import unpack

from hypernets.binary.libhypstar import Hypstar, radiometer, entrance
from hypernets.binary.libhypstar import s_img_data


def take_picture(path_to_picture=None, params=None):
    # Note : 'params = None' for now, only 5MP is working

    if path_to_picture is None:
        from os import path
        path_to_picture = datetime.utcnow().strftime("%Y%m%dT%H%M%S.jpg")
        path_to_picture = path.join("DATA", path_to_picture)

    try:
        hs = Hypstar("/dev/ttyUSB5")
        im_data = s_img_data()
        hs.acquireDefaultJpeg(True, False, im_data)
        stream = im_data.jpeg_to_bytes()
        with open(path_to_picture, 'wb') as f:
            f.write(stream)
        print(f"Saved to {path_to_picture}.")
        return True

    except Exception as e:
        print(f"Error : {e}")
        return e


def take_spectra(path_to_file, mode, action, it_vnir, it_swir, cap_count):

    rad = {'vis': radiometer.VNIR, 'swi': radiometer.SWIR,
           'bot': radiometer.BOTH}[mode]

    ent = {'rad': entrance.RADIANCE, 'irr': entrance.IRRADIANCE,
           'bla': entrance.DARK}[action]

    print(f"--> [{rad} {ent} {it_vnir} {it_swir}] x {cap_count}")

    try:
        hs = Hypstar('/dev/ttyUSB5')

    except Exception as e:
        print(f"Error : {e}")
        return e

    try:
        cap_list = hs.acquireSpectra(rad, ent, it_vnir, it_swir, cap_count, 0)

        if len(cap_list) == 0:
            return Exception()

        # Concatenation
        spectra = b''
        for n, spectrum in enumerate(cap_list):
            spectra += spectrum.getRawData()
            print(f"Spectrum #{n} added")

        # Save
        with open(path_to_file, "wb") as f:
            f.write(spectra)

        print(f"Saved to {path_to_file}.")

    except Exception as e:
        print(f"Error : {e}")
        return e

    # Read AIT Time from first spectrum in data
    if it_vnir == 0 and mode == "vis":
        it_vnir, = unpack('<H', spectra[11:13])

    if it_swir == 0 and mode == "swi":
        it_swir, = unpack('<H', spectra[11:13])

    if action != "bla" and mode == "bot" and it_swir == 0 and it_vnir == 0:
        print("Warning : do not try dark just after double zero IT")
        print("(not implemented)")
        first_it, = unpack('<H', spectra[11:13])
        it_swir = first_it
        it_vnir = first_it

    return it_vnir, it_swir
