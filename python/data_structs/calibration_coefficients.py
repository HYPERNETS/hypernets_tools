from _ctypes import Structure
from ctypes import c_double, c_int16, c_uint32, c_uint16, c_uint8, c_float


class CalibrationCoefficients(Structure):
	_pack_ = 1
	_fields_ = [
		('vnir_wavelength_coefficients', 6 * c_double),
		('vnir_lin_coefs', 8 * c_double),
		('swir_wavelength_coefs', 5 * c_double),
		('accelerometer_horizontal_reference', 3 * c_int16)
	]

	def __str__(self):
		return '\nVIS-NIR wavelength coefficients:\t' \
			   'A: {: <14} B1: {: <14} B2: {: <14} B3: {: <14} B4: {: <14} B5: {: <14}\n' \
			   'VIS-NIR linearity coefficients:\t\t' \
			   'A: {: <14} B1: {: <14} B2: {: <14} B3: {: <14} B4: {: <14} B5: {: <14} B6: {: <14} B7: {: <14}\n' \
			   'SWIR wavelength coefficients:\t\t' \
			   'A: {: <14} B1: {: <14} B2: {: <14} B3: {: <14} B4: {: <14}\n' \
			   'Accelerometer horisontal refrence:\t' \
			   'X: {}, \tY: {}, \tZ: {}\n' \
			.format(
			self.vnir_wavelength_coefficients[0], self.vnir_wavelength_coefficients[1], self.vnir_wavelength_coefficients[2], self.vnir_wavelength_coefficients[3], self.vnir_wavelength_coefficients[4], self.vnir_wavelength_coefficients[5],
			self.vnir_lin_coefs[0], self.vnir_lin_coefs[1], self.vnir_lin_coefs[2], self.vnir_lin_coefs[3], self.vnir_lin_coefs[4], self.vnir_lin_coefs[5], self.vnir_lin_coefs[6], self.vnir_lin_coefs[7],
			self.swir_wavelength_coefs[0], self.swir_wavelength_coefs[1], self.swir_wavelength_coefs[2], self.swir_wavelength_coefs[3], self.swir_wavelength_coefs[4],
			self.accelerometer_horizontal_reference[0], self.accelerometer_horizontal_reference[1], self.accelerometer_horizontal_reference[2]
		)


class ExtendedCalibrationCoefficients(Structure):
	_pack_ = 1
	_fields_ = [
		('instrument_serial_number', c_uint32),
		('calibration_year', c_uint16),
		('calibration_month', c_uint8),
		('calibration_day', c_uint8),
		('accelerometer_horizontal_reference', 3 * c_int16),
		('vnir_nonlinearity_coefficients', 4 * c_float),
		('vnir_coefficients_L', 2048 * c_float),
		('vnir_coefficients_E', 2048 * c_float),
		('swir_nonlinearity_coefficients', 9 * c_float),
		('swir_coefficients_L', 256 * c_float),
		('swir_coefficients_E', 256 * c_float),
		('crc32', c_uint32)
	]