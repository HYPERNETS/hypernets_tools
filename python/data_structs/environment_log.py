from _ctypes import Structure
from ctypes import c_uint64, c_int16, c_uint16, c_int32, c_float
from datetime import datetime


class PowerBusInfo:
	voltage = 0.0
	current = 0.0
	total_energy = 0.0

	def __init__(self):
		self.voltage = 0.0
		self.current = 0.0
		self.total_energy = 0.0

	def __str__(self):
		return 'Voltage: \t{0: .4f} V,\t\tcurrent: \t{1: .4f} A,\t\ttotal energy consumed:\t{2: .4f} mWh'.format(self.voltage, self.current, self.total_energy)

	def parse(self, name, logentry):
		exec('self.voltage = logentry.voltage_' + name)
		exec('self.current = logentry.current_' + name)
		exec('self.total_energy = logentry.energy_' + name)
		return self


class AccelerationInfo:
	x_raw = 0
	y_raw = 0
	z_raw = 0
	x_g = 0
	y_g = 0
	z_g = 0

	def __init__(self):
		self.x_raw = 0
		self.y_raw = 0
		self.z_raw = 0
		self.x_g = 0
		self.y_g = 0
		self.z_g = 0

	def __str__(self):
		return 'Acceleration: X: {}, Y: {}, Z: {}'.format(self.x_raw, self.y_raw, self.z_raw)

	def parse(self, logentry):
		self.x_raw = logentry.accelerometer_readings_XYZ[0]
		self.y_raw = logentry.accelerometer_readings_XYZ[1]
		self.z_raw = logentry.accelerometer_readings_XYZ[2]
		return self


class EnvironmentLogEntry(Structure):
	_pack_ = 1
	_fields_ = [
		('timestamp', c_uint64),
		('humidity_sensor_temperature', c_int16),
		('humidity_sensor_humidity', c_uint16),
		('pressure_sensor_pressure', c_int32),
		('pressure_sensor_temperature', c_int32),
		('accelerometer_readings_XYZ', c_int16 * 3),
		('internal_ambient_temperature', c_float),
		('swir_body_temperature', c_float),
		('swir_heatsink_temperature', c_float),
		('energy_common_3v3', c_float),
		('energy_mcu_3v3', c_float),
		('energy_camera_3v3', c_float),
		('voltage_common_3v3', c_float),
		('voltage_mcu_3v3', c_float),
		('voltage_camera_3v3', c_float),
		('current_common_3v3', c_float),
		('current_mcu_3v3', c_float),
		('current_camera_3v3', c_float),
		('energy_swir_module_12v', c_float),
		('energy_multiplexer_12v', c_float),
		('energy_vnir_module_5v', c_float),
		('energy_input_12v', c_float),
		('voltage_swir_module_12v', c_float),
		('voltage_multiplexer_12v', c_float),
		('voltage_vnir_module_5v', c_float),
		('voltage_input_12v', c_float),
		('current_swir_module_12v', c_float),
		('current_multiplexer_12v', c_float),
		('current_vnir_module_5v', c_float),
		('current_input_12v', c_float),
	]

	def parse(self):
		self.humidity_sensor_temp = self.humidity_sensor_temperature / 100
		self.humidity = self.humidity_sensor_humidity/10
		self.pressure_sensor_temp = self.pressure_sensor_temperature / 100
		self.pressure = self.pressure_sensor_pressure / 10
		self.internal_ambient_temp = self.internal_ambient_temperature
		self.swir_body_temperatureemp = self.swir_body_temperature if self.swir_body_temperature > -40 else 'N/A'
		self.swir_heatsink_temperatureemp = self.swir_heatsink_temperature if self.swir_heatsink_temperature > -40 else 'N/A'
		self.input_12V = PowerBusInfo().parse('input_12v', self)
		self.optical_multiplexer_12V = PowerBusInfo().parse('multiplexer_12v', self)
		self.swir_12V = PowerBusInfo().parse('swir_module_12v', self)
		self.vnir_5V = PowerBusInfo().parse('vnir_module_5v', self)
		self.common_3V3 = PowerBusInfo().parse('common_3v3', self)
		self.digital_electronics_3V3 = PowerBusInfo().parse('mcu_3v3', self)
		self.camera_3V3 = PowerBusInfo().parse('camera_3v3', self)
		self.accelerometer_data = AccelerationInfo().parse(self)

	def __str__(self):
		return 'TS: {} ({})\n' \
			   'Temperatures:\n ' \
			   '\tInternal: {:.2f}, Humidity sensor: {}, Pressure sensor: {}\n' \
			   '\tSWIR body: {:.2f}, SWIR heatsink: {:.2f}\n' \
			   'RH: {}%, internal pressure: {} mBar\n' \
			   'Power buses:\n' \
			   '\t12 V input: \t\t{}\n' \
			   '\t12 V Multiplexer: \t{}\n' \
			   '\t12 V SWIR: \t\t\t{}\n' \
			   '\t5 V VIS-NIR: \t\t{}\n' \
			   '\t3.3 V common: \t\t{}\n' \
			   '\t3.3 V digital: \t\t{}\n' \
			   '\t3.3 V camera: \t\t{}\n' \
			   '{}'.format(self.timestamp, datetime.utcfromtimestamp(int(self.timestamp / 1000)),
						   self.internal_ambient_temp, self.humidity_sensor_temp, self.pressure_sensor_temp,
						   self.swir_body_temperature, self.swir_heatsink_temperature,
						   self.humidity, self.pressure,
						   self.input_12V, self.optical_multiplexer_12V, self.swir_12V, self.vnir_5V, self.common_3V3, self.digital_electronics_3V3, self.camera_3V3,
						   self.accelerometer_data)
