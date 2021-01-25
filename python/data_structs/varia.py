from _ctypes import Structure
from ctypes import c_uint16

from data_structs.spectrum_raw import OpticalConfiguration


class HypstarAutoITStatus(Structure):
	_pack_ = 1
	_fields_ = [
		("spectrum_config", OpticalConfiguration),	# LSB of flags byte, should be 0
		("current_integration_time_ms", c_uint16),
		("peak_adc_value", c_uint16),
		("next_integration_time_ms", c_uint16),
		("memory_slot_id", c_uint16)
	]
