from _ctypes import Structure
from ctypes import c_uint8, c_uint16, c_int, c_uint32, c_byte, c_char

MAX_IMG_W = 2592
MAX_IMG_H = 1944
IMG_SIZE_MAX = MAX_IMG_W * MAX_IMG_H


class HypstarImage(Structure):
	_pack_ = 1
	_fields_ = [
		("image_type", c_uint8),
		("image_data_jpeg", IMG_SIZE_MAX * c_uint16),
		("image_size", c_uint32),
		("crc32_spaceholder", c_uint32)
	]
