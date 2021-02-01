import struct
from ctypes import *
from enum import IntEnum

from data_structs.hardware_info import BootedPacketStruct, HypstarSupportedBaudRates
from data_structs.calibration_coefficients import CalibrationCoefficients, ExtendedCalibrationCoefficients
from data_structs.environment_log import EnvironmentLogEntry
from data_structs.image import HypstarImage
from data_structs.spectrum_raw import RadiometerEntranceType, RadiometerType, HypstarSpectrum
from data_structs.varia import HypstarAutoITStatus


class HypstarLogLevel(IntEnum):
	ERROR = 0
	WARNING = 1
	INFO = 2
	DEBUG = 3
	TRACE = 4

	def __init__(self, value):
		self._as_parameter = int(value)

	# needed for CTypes passing as argument
	@classmethod
	def from_param(cls, obj):
		return int(obj)


class Hypstar:
	handle = None
	lib = None
	hw_info = None

	def __init__(self, port):
		self.lib = CDLL('libhypstar.so')
		port = create_string_buffer(bytes(port, 'ascii'))
		self.define_argument_types()
		self.handle = self.lib.hypstar_init(port)
		if not self.handle:
			raise IOError("Could not retrieve instrument instance!")
		self.get_hw_info()

	def __del__(self):
		self.lib.hypstar_close(self.handle)

	def set_log_level(self, loglevel):
		self.lib.hypstar_set_loglevel(self.handle, loglevel)

	def get_hw_info(self):
		self.hw_info = BootedPacketStruct()
		r = self.lib.hypstar_get_hw_info(self.handle, pointer(self.hw_info))
		if not r:
			print('Could not retrieve hardware information from the instrument')

	def reboot(self):
		r = self.lib.hypstar_reboot(self.handle)
		if not r:
			raise Exception("Did not get booted packet, reboot unsucessful")
		return r

	def set_baud_rate(self, baudrate):
		if type(baudrate) is not HypstarSupportedBaudRates:
			raise ValueError("Bad baud rate provided")
		r = self.lib.hypstar_set_baudrate(self.handle, baudrate)
		if not r:
			raise Exception("Did not succeed in switching baud rate")

	# returns instrument internal UNIX timestamp in milliseconds since 01.01.1970
	# millisecond resolution provided to distinguish spectra taken with sub-second integration time
	def get_time_ms(self):
		ts = self.lib.hypstar_get_time(self.handle)
		return ts

	# sets clock of the instrument, used for timestamping spectra
	# input expected: UNIX timestamp in seconds (seconds passed since 01.01.1970
	def set_time_s(self, ts):
		self.lib.hypstar_set_time(self.handle, c_uint64(ts))

	def get_env_log(self, index=0):
		itm = EnvironmentLogEntry()
		r = self.lib.hypstar_get_env_log(self.handle, index, pointer(itm))
		if not r:
			raise Exception('Could not retrieve environmental log')
		itm.parse()
		return itm

	def get_calibration_coeficients_basic(self):
		itm = CalibrationCoefficients()
		r = self.lib.hypstar_get_calibration_coefficients_basic(self.handle, pointer(itm))
		if not r:
			raise Exception('Could not get calibration coefficients')
		return itm

	def get_calibration_coeficients_extended(self):
		itm = ExtendedCalibrationCoefficients()
		r = self.lib.hypstar_get_calibration_coefficients_extended(self.handle, pointer(itm))
		if not r:
			raise Exception('Could not get extended calibration coefficients')
		return itm

	def get_calibration_coeficients_all(self):
		itm = CalibrationCoefficients()
		itm2 = ExtendedCalibrationCoefficients()
		r = self.lib.hypstar_get_calibration_coefficients_all(self.handle, pointer(itm), pointer(itm2))
		if not r:
			raise Exception('Could not get all calibration coefficients')
		return (itm, itm2)

	# 1s or 100ms limit with 100ms integration time will return only 9 items, since there's ~2ms overhead for capture and download
	# when switching from one entrance type to another with time limit set, less than theoretical maximum number of spectra will be captured
	# this is due to optical multiplexer physical movement taking some time (~300 ms)
	def capture_spectra(self, spectrum_type, entrance, vnir_int_time_ms, swir_int_time_ms, scan_count, series_time_max_s):
		return self.lib.hypstar_capture_spectra(self.handle, spectrum_type, entrance, vnir_int_time_ms, swir_int_time_ms, scan_count, series_time_max_s)

	def get_last_capture_spectra_memory_slots(self, count):
		slots = (c_uint16 * count)()
		r = self.lib.hypstar_get_last_capture_memory_slots(self.handle, pointer(slots), count)
		if r != count:
			raise Exception('Wrong slot count in GET_SLOTS response')
		return slots

	def download_spectra(self, memory_slots):
		spectra = (HypstarSpectrum * (len(memory_slots)))()
		r = self.lib.hypstar_download_spectra(self.handle, memory_slots, len(memory_slots), pointer(spectra))
		if r != len(memory_slots):
			raise Exception('Did not get enough spectra')
		return spectra

	# currently returns size in data packets, not bytes
	def capture_JPEG_image(self, flip=False, mirror=False, scale=False):
		self.lib.hypstar_capture_JPEG_image(self.handle, flip, mirror)

	# returns properly formatted JPEG image as a byte stream
	def download_JPEG_image(self):
		img = HypstarImage()
		size = self.lib.hypstar_download_JPEG_image(self.handle, pointer(img))
		fmt = "<{}H".format(int(size))
		bin = struct.pack(fmt, *img.image_data_jpeg[:size])
		return bin

	def set_SWIR_module_temperature(self, target_C):
		r = self.lib.hypstar_set_TEC_target_temperature(self.handle, target_C)
		if not r:
			raise Exception("Could not set target temperature")
		return r

	def shutdown_SWIR_module_thermal_control(self):
		r = self.lib.hypstar_shutdown_TEC(self.handle)
		if not r:
			raise Exception("Did not succedd in shutting down SWIR TEC")
		return r

	def define_argument_types(self):
		self.lib.hypstar_init.restype = c_void_p
		self.lib.hypstar_close.argtypes = [c_void_p]
		self.lib.hypstar_get_hw_info.argtypes = [c_void_p]
		self.lib.hypstar_set_loglevel.argtypes = [c_void_p, HypstarLogLevel]
		self.lib.hypstar_reboot.argtypes = [c_void_p]
		self.lib.hypstar_set_baudrate.argtypes = [c_void_p, HypstarSupportedBaudRates]
		self.lib.hypstar_get_time.argtypes = [c_void_p]
		self.lib.hypstar_get_time.restype = c_uint64
		self.lib.hypstar_set_time.argtypes = [c_void_p, c_uint64]
		self.lib.hypstar_get_env_log.argtypes = [c_void_p, c_uint8, c_void_p]
		self.lib.hypstar_get_calibration_coefficients_basic.argtypes = [c_void_p, c_void_p]
		self.lib.hypstar_get_calibration_coefficients_extended.argtypes = [c_void_p, c_void_p]
		self.lib.hypstar_get_calibration_coefficients_all.argtypes = [c_void_p, c_void_p, c_void_p]
		self.lib.hypstar_capture_spectra.argtypes = [c_void_p, RadiometerType, RadiometerEntranceType, c_uint16, c_uint16, c_uint16, c_uint16]
		self.lib.hypstar_get_last_capture_memory_slots.argtypes = [c_void_p, c_void_p, c_uint16]
		self.lib.hypstar_download_spectra.argtypes = [c_void_p, c_void_p, c_uint16, c_void_p]
		self.lib.hypstar_capture_JPEG_image.argtypes = [c_void_p, c_bool, c_bool]
		self.lib.hypstar_download_JPEG_image.argtypes = [c_void_p, c_void_p]
		self.lib.hypstar_set_TEC_target_temperature.argtypes = [c_void_p, c_float]
		self.lib.hypstar_shutdown_TEC.argtypes = [c_void_p]

	def callback_test_fn(self, it_status):
		print(type(it_status))
		print("Got callback {} {} {} {}".format(it_status.contents.this_inttme_ms, it_status.contents.next_inttme_ms, it_status.contents.na, it_status.contents.vnir))

	def register_callback(self):
		cb_func_def = CFUNCTYPE(c_void_p, POINTER(HypstarAutoITStatus))
		cb_func = cb_func_def(self.callback_test_fn)
		self.lib.hypstar_test_callback(self.handle, cb_func, 1, 2)
