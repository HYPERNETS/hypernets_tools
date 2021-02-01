from _ctypes import Structure
from ctypes import c_uint16, c_uint8, c_uint64, c_float, c_int16, c_uint32
from datetime import datetime
from enum import IntEnum

from .spectrum import Spectrum


class RadiometerType(IntEnum):
	VIS_NIR = 1
	SWIR = 2
	BOTH = 3

	def __init__(self, value):
		self._as_parameter = int(value)

	# needed for CTypes passing as argument
	@classmethod
	def from_param(cls, obj):
		return int(obj)


class RadiometerEntranceType(IntEnum):
	DARK = 0
	RADIANCE = 1
	IRRADIANCE = 2

	def __init__(self, value):
		self._as_parameter = int(value)

	# needed for CTypes passing as argument
	@classmethod
	def from_param(cls, obj):
		return int(obj)


class OpticalConfiguration(Structure):
	_pack_ = 1
	_fields_ = [
		("na", c_uint8, 3),	# LSB of flags byte, should be 0
		("irradiance", c_uint8, 1),
		("radiance", c_uint8, 1),
		("semolator_fake_saturation", c_uint8, 1),	# should be 0, not implemented
		("swir", c_uint8, 1),
		("vnir", c_uint8, 1),
	]


class AccelerationStatisticsEntry(Structure):
	_pack_ = 1
	_fields_ = [
		("mean_acceleration", c_int16),
		("standard_deviation", c_int16)
	]

	def __str__(self):
		return "{} ± {}".format(self.mean_acceleration, self.standard_deviation)


class AccelerationStatistics(Structure):
	_pack_ = 1
	_fields_ = [
		("X", AccelerationStatisticsEntry),
		("Y", AccelerationStatisticsEntry),
		("Z", AccelerationStatisticsEntry)
	]

	def __str__(self):
		return "Acceleration statistics:\n \tX: {}\n \tY: {}\n \tZ: {}\n".format(self.X, self.Y, self.Z)


class SpectrumHeader(Structure):
	_pack_ = 1
	_fields_ = [
		("dataset_total_length", c_uint16),
		("spectrum_config", OpticalConfiguration),
		("timestamp_ms", c_uint64),
		("integration_time_ms", c_uint16),
		("sensor_temperature", c_float),
		("pixel_count", c_uint16),
		("acceleration_statistics", AccelerationStatistics),
	]


class HypstarSpectrum(Structure):
	_pack_ = 1
	_fields_ = [
		("spectrum_header", SpectrumHeader),
		("spec", 2048 * c_uint16),
		("crc32_spaceholder", c_uint32)
	]

	def __str__(self):
		return "Spectrum timestamp: {} ({} UTC)\n" \
			   "Radiometer VIS: {}, SWIR: {}\n" \
			   "Entrance L: {}, E: {}\n" \
			   "Integration time: {} ms\n" \
			   "Pixel count: {}\n" \
			   "Sensor temperature: {:.2f}\n" \
			   "{}" \
			   "CRC32: {}\n"\
			.format(
			self.spectrum_header.timestamp_ms, datetime.utcfromtimestamp(int(self.spectrum_header.timestamp_ms/1000)).strftime('%Y-%m-%d %H:%M:%S'),
			self.spectrum_header.spectrum_config.vnir, self.spectrum_header.spectrum_config.swir,
			self.spectrum_header.spectrum_config.radiance, self.spectrum_header.spectrum_config.irradiance,
			self.spectrum_header.integration_time_ms,
			self.spectrum_header.pixel_count,
			self.spectrum_header.sensor_temperature,
			self.spectrum_header.acceleration_statistics,
			hex(self.crc32_spaceholder)
		)

	def convert_to_spectrum_class(self):
		return Spectrum.parse_raw(bytes(self))

	# Due to C/CTypes limitation, SWIR spectrum contains 2048 pixels instead of 256 with most of them 0, so we cut out unnecessary data when packing
	def getBytes(self):
		whole = bytes(self)
		return whole[:self.spectrum_header.dataset_total_length-4] + whole[len(whole)-4:]
