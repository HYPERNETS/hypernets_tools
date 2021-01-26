import io
import unittest

from PIL import Image

from data_structs.hardware_info import HypstarSupportedBaudRates
from data_structs.spectrum_raw import RadiometerType, RadiometerEntranceType
from hypstar_wrapper import Hypstar, HypstarLogLevel

serial_port = '/dev/ttyUSB0'


class CtypeTests(unittest.TestCase):

	def test_hw_info(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_log_level(HypstarLogLevel.DEBUG)
		radiometer.set_log_level(HypstarLogLevel.TRACE)
		print(radiometer.hw_info)

	def test_reboot(self):
		radiometer = Hypstar(serial_port)
		assert radiometer.reboot() == 1

	def test_double_instantiation_should_return_same_handle(self):
		radiometer = Hypstar(serial_port)
		radiometer2 = Hypstar(serial_port)
		assert radiometer.handle == radiometer2.handle

	def test_baud_rate_changing_valid(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_baud_rate(HypstarSupportedBaudRates.B_3000000)
		radiometer.get_hw_info()
		del radiometer
		# test that baud rate got reset after reinit
		radiometer = Hypstar(serial_port)
		radiometer.get_hw_info()

	def test_baud_rate_invalid_should_throw(self):
		radiometer = Hypstar(serial_port)
		try:
			radiometer.set_baud_rate(123456)
		except ValueError as e:
			assert str(e) == "Bad baud rate provided"

	def test_env_log(self):
		radiometer = Hypstar(serial_port)
		log = radiometer.get_env_log()
		print(log)

	def test_env_right_after_boot(self):
		radiometer = Hypstar(serial_port)
		radiometer.reboot()
		log = radiometer.get_env_log()
		print(log)

	def test_time(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_log_level("DEBUG")
		ts_in = 1234578790
		radiometer.set_time_s(ts_in)
		ts_out = radiometer.get_time_ms()
		print('\n\rExecution time: {} ms'.format(int(ts_out - ts_in*1000)))

	def test_calibration_coefficients(self):
		radiometer = Hypstar(serial_port)
		# radiometer.set_log_level("TRACE")
		coefficients = radiometer.get_calibration_coeficients_basic()
		print(coefficients)
		extended_coefficients = radiometer.get_calibration_coeficients_extended()
		basic, extended_coefficients = radiometer.get_calibration_coeficients_all()

	def test_start_SWIR_TEC(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_SWIR_module_temperature(-5.23)

	def test_shutdown_SWIR_TEC(self):
		radiometer = Hypstar(serial_port)
		radiometer.shutdown_SWIR_module_thermal_control()

	def test_capture_spectrum_fixed_it_vis(self):
		radiometer = Hypstar(serial_port)
		count = radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.DARK, 100, 0, 1, 0)
		assert count == 1
		count = radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.RADIANCE, 100, 0, 2, 0)
		assert count == 2
		count = radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.IRRADIANCE, 100, 0, 1, 0)
		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		print(slots[0])
		assert len(slots) == count
		spectra = radiometer.download_spectra(slots)
		print(spectra[0])
		for i in range(spectra[0].spectrum_header.pixel_count):
			print("{}: {}".format(i, spectra[0].spec[i]))
		assert (spectra[0].spectrum_header.spectrum_config.vnir == 1)
		assert (spectra[0].spectrum_header.spectrum_config.swir == 0)
		assert (spectra[0].spectrum_header.spectrum_config.radiance == 0)
		assert (spectra[0].spectrum_header.spectrum_config.irradiance == 1)
		assert (spectra[0].spectrum_header.pixel_count == 2048)
		assert (spectra[0].spectrum_header.integration_time_ms == 100)

	def test_capture_spectrum_fixed_it_swir(self):
		radiometer = Hypstar(serial_port)
		if not radiometer.hw_info.swir_module_available:
			print('SWIR module not available')
			pass

		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.DARK, 0, 100, 1, 0)
		assert count == 1
		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.RADIANCE, 0, 100, 2, 0)
		assert count == 2
		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.IRRADIANCE, 0, 100, 0, 1)
		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		assert len(slots) == count
		spectra = radiometer.download_spectra(slots)
		print(spectra[0])
		for i in range(spectra[0].spectrum_header.pixel_count):
			print("{}: {}".format(i, spectra[0].spec[i]))

		assert (spectra[0].spectrum_header.spectrum_config.vnir == 0)
		assert (spectra[0].spectrum_header.spectrum_config.swir == 1)
		assert (spectra[0].spectrum_header.spectrum_config.radiance == 0)
		assert (spectra[0].spectrum_header.spectrum_config.irradiance == 1)
		assert (spectra[0].spectrum_header.pixel_count == 256)
		assert (spectra[0].spectrum_header.integration_time_ms == 100)

	def test_capture_spectrum_fixed_it_both(self):
		radiometer = Hypstar(serial_port)
		if not radiometer.hw_info.swir_module_available:
			print('SWIR module not available')
			pass

		count = radiometer.capture_spectra(RadiometerType.BOTH, RadiometerEntranceType.DARK, 100, 100, 1, 0)
		assert count == 2
		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.RADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.BOTH, RadiometerEntranceType.RADIANCE, 100, 100, 2, 0)
		assert count == 4
		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.IRRADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.BOTH, RadiometerEntranceType.IRRADIANCE, 450, 450, 0, 1)
		assert count == 4
		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		assert len(slots) == count
		spectra = radiometer.download_spectra(slots)

	def test_capture_spectrum_auto_it_VIS(self):
		radiometer = Hypstar(serial_port)
		if not radiometer.hw_info.swir_module_available:
			print('SWIR module not available')
			pass

		count = radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.DARK, 0, 0, 1, 0)
		assert count == 1
		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.RADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.RADIANCE, 0, 0, 2, 0)
		assert count == 2
		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.IRRADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.VIS_NIR, RadiometerEntranceType.IRRADIANCE, 0, 0, 4, 0)
		assert count == 4
		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		assert len(slots) == count
		spectra = radiometer.download_spectra(slots)

	def test_capture_spectrum_auto_it_SWIR(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_log_level("DEBUG")
		if not radiometer.hw_info.swir_module_available:
			print('SWIR module not available')
			pass

		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.RADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.RADIANCE, 0, 0, 2, 0)
		assert count == 2
		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.IRRADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.IRRADIANCE, 0, 0, 4, 0)

		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.DARK, 0, 0, 1, 0)
		assert count == 1

		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		assert len(slots) == count
		spectra = radiometer.download_spectra(slots)

	def test_capture_spectrum_auto_it_BOTH(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_log_level("DEBUG")
		if not radiometer.hw_info.swir_module_available:
			print('SWIR module not available')
			pass

		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.RADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.RADIANCE, 0, 0, 2, 0)
		assert count == 2
		# rotate to correctly predict count
		radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.IRRADIANCE, 10, 0, 1, 0)
		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.IRRADIANCE, 0, 0, 4, 0)

		count = radiometer.capture_spectra(RadiometerType.SWIR, RadiometerEntranceType.DARK, 0, 0, 1, 0)
		assert count == 1

		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		assert len(slots) == count
		spectra = radiometer.download_spectra(slots)

	def test_capture_spectrum_and_convert(self):
		radiometer = Hypstar(serial_port)
		radiometer.set_log_level("DEBUG")

		radiometer.set_SWIR_module_temperature(-5.0)
		count = radiometer.capture_spectra(RadiometerType.BOTH, RadiometerEntranceType.DARK, 0, 0, 3, 0)
		slots = radiometer.get_last_capture_spectra_memory_slots(count)
		spectra = radiometer.download_spectra(slots)
		for i in spectra:
			print(i)
			s = i.convert_to_spectrum_class()  # Type: Spectrum
			# s.plot()

	def test_capture_JPEG(self):
		radiometer = Hypstar(serial_port)
		radiometer.capture_JPEG_image(flip=True, mirror=False)
		radiometer.set_baud_rate(HypstarSupportedBaudRates.B_6000000)

		img = radiometer.download_JPEG_image()
		stream = io.BytesIO(img)
		im = Image.open(stream)
		w, h = im.size
		print("Image size: {} x {}".format(w, h))
		im.show()

	def test_register_callback(self):
		radiometer = Hypstar(serial_port)
		radiometer.register_callback()


if __name__ == '__main__':
	unittest.main()
