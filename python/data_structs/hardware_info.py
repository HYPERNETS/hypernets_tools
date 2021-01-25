from _ctypes import Structure
from ctypes import c_uint8, c_uint32, c_uint16, c_int
from enum import IntEnum


class HypstarSupportedBaudRates(IntEnum):
	B_115200 = 115200
	B_460800 = 460800
	B_921600 = 921600
	B_3000000 = 3000000
	B_6000000 = 6000000
	B_8000000 = 8000000

	def __init__(self, value):
		self._as_parameter = int(value)

	# needed for CTypes passing as argument
	@classmethod
	def from_param(cls, obj):
		return int(obj)

class BootedPacketStruct(Structure):
	_pack_ = 1
	_fields_ = [
		("firmware_version_major", c_uint8),
		("firmware_version_minor", c_uint8),
		("firmware_version_revision", c_uint8),
		("instrument_serial_number", c_uint32),
		("mcu_hardware_version", c_uint8),
		("psu_hardware_version", c_uint8),
		("vis_serial_number", c_uint16),
		("swir_serial_number", c_uint32),
		("memory_slot_count", c_uint16),
		("vnir_module_available", c_uint16, 1),
		("swir_module_available", c_uint16, 1),
		("optical_multiplexer_available", c_uint16, 1),
		("camera_available", c_uint16, 1),
		("accelerometer_available", c_uint16, 1),
		("humidity_sensor_available", c_uint16, 1),
		("pressure_sensor_available", c_uint16, 1),
		("swir_tec_module_available", c_uint16, 1),
		("sd_card_available", c_uint16, 1),
		("power_monitor_1_available", c_uint16, 1),
		("power_monitor_2_available", c_uint16, 1),
	]

	def __str__(self):
		return "FW: {}.{}.{}, \n" \
			   "instrument S/N: {},\n" \
			   "MCU HW V: {}, PSU HW V: {}\n" \
			   "VIS SPEC S/N: {}\n" \
			   "SWIR_SPEC S/N: {}\n" \
			   "memory slots available: {} \n" \
			   "available hardware:\n" \
			   "VIS: {}\n" \
			   "SIWR: {}\n" \
			   "MUX: {}\n" \
			   "CAM: {}\n" \
			   "accelerometer: {}\n" \
			   "Humidity sensor: {}\n" \
			   "Pressure sensor: {}\n" \
			   "SWIR TEC: {}\n" \
			   "SD Card: {}\n" \
			   "Power monitor 1: {}\n" \
			   "Power monitor 2: {}\n".format(
			   self.firmware_version_major, self.firmware_version_minor, self.firmware_version_revision, hex(self.instrument_serial_number),
				self.mcu_hardware_version, self.psu_hardware_version,
				self.vis_serial_number, self.swir_serial_number, self.memory_slot_count,
				self.vnir_module_available, self.swir_module_available, self.optical_multiplexer_available, self.camera_available,
				self.accelerometer_available, self.humidity_sensor_available, self.pressure_sensor_available,
				self.swir_tec_module_available, self.sd_card_available, self.power_monitor_1_available, self.power_monitor_2_available)