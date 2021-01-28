#include <iostream>
#include <iomanip>
#include <assert.h>

#include "../inc/hypstar.h"

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB0";
	Hypstar *hs = Hypstar::getInstance(port);
	s_environment_log_entry log, log2;
	hs->setLoglevel(DEBUG);

	hs->getEnvironmentLogEntry(&log, 0);
	hs->getEnvironmentLogEntry(&log2, 1);
	// log2 has to be older
	assert(log2.timestamp < log.timestamp);
	time_t t = log.timestamp / 1000;
	auto tm = *localtime(&t);

	cout << "Timestamp: " << log.timestamp << " (" << put_time(&tm, "%Y-%m-%d %H:%M:%S") << ")\n";
	cout << setw(30) << left << "Temp RH ('C):" << log.humidity_sensor_temperature << "\n";
	cout << setw(30) << left << "Temp Pressure ('C):" << log.pressure_sensor_temperature << "\n";
	cout << setw(30) << left << "Temp ambient ('C):" << log.internal_ambient_temperature << "\n";
	cout << setw(30) << left << "Temp SWIR body ('C):" << log.swir_body_temperature << "\n";
	cout << setw(30) << left << "Temp SWIR sink ('C):" << log.swir_heatsink_temperature << "\n";
	cout << setw(30) << left << "RH (%):" << log.humidity_sensor_humidity << "\n";
	cout << setw(30) << left << "Pressure (mbar)\t" << log.pressure_sensor_pressure << "\n";

	cout << setw(30) << left << "E common (mWh):" << log.energy_common_3v3 << "\n";
	cout << setw(30) << left << "E e_cam_3v3 (mWh):" << log.energy_camera_3v3 << "\n";
	cout << setw(30) << left << "E e_mcu_3v3 (mWh):" << log.energy_mcu_3v3 << "\n";
	cout << setw(30) << left << "E e_swir_12v (mWh):" << log.energy_swir_module_12v << "\n";
	cout << setw(30) << left << "E e_mux_12v (mWh):" << log.energy_multiplexer_12v << "\n";
	cout << setw(30) << left << "E e_vnir_5v (mWh):" << log.energy_vnir_module_5v << "\n";
	cout << setw(30) << left << "E e_input_12v (mWh):" << log.energy_input_12v << "\n";

	cout << setw(30) << left << "i_common_3v3:" << log.current_common_3v3 << "\n";
	cout << setw(30) << left << "i_mcu_3v3:" << log.current_mcu_3v3 << "\n";
	cout << setw(30) << left << "i_cam_3v3:" << log.current_camera_3v3 << "\n";
	cout << setw(30) << left << "i_swir_12v:" << log.current_swir_module_12v << "\n";
	cout << setw(30) << left << "i_mux_12v:" << log.current_multiplexer_12v << "\n";
	cout << setw(30) << left << "i_vnir_5v:" << log.current_vnir_module_5v << "\n";
	cout << setw(30) << left << "i_input_12v:" << log.current_input_12v << "\n";

	cout << setw(30) << left << "u_common_3v3:" << log.voltage_common_3v3 << "\n";
	cout << setw(30) << left << "u_cam_3v3:" << log.voltage_camera_3v3 << "\n";
	cout << setw(30) << left << "u_mcu_3v3:" << log.voltage_mcu_3v3 << "\n";
	cout << setw(30) << left << "u_swir_12v:" << log.voltage_swir_module_12v << "\n";
	cout << setw(30) << left << "u_mux_12v:" << log.voltage_multiplexer_12v << "\n";
	cout << setw(30) << left << "u_vnir_5v:" << log.voltage_vnir_module_5v << "\n";
	cout << setw(30) << left << "u_input_12v:" << log.voltage_input_12v << "\n";
	cout << "Acceleration:" << endl;
	cout << "\tX:" << setw(30) << log.accelerometer_readings_XYZ[0] << endl;
	cout << "\tY:" << setw(30) << log.accelerometer_readings_XYZ[1] << endl;
	cout << "\tZ:" << setw(30) << log.accelerometer_readings_XYZ[2] << endl;

	printf("--------------\nC++ Test pass\n");

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	s_environment_log_entry env_log;
	hypstar_get_env_log(pHs, 0, &env_log);
	assert (log.timestamp == env_log.timestamp);
	printf("--------------\nC Test pass\n");
}
