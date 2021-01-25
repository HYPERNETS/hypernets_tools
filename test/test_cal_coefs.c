#include <iostream>

#include "../inc/hypstar.h"

using namespace std;

template <typename T>
void print_array(const char* name, T *ptr, int count)
{
	std::cout << name << ": \n";
	for (int i = 0; i < count; i++)
	{
	    std::cout << "\t" << i+1 << ":" << ptr[i] << "\n";
	}

}

int main() {
	std::string port = "/dev/ttyUSB1";
	Hypstar *hs = Hypstar::getInstance(port);
	hs->setLoglevel(DEBUG);

	hs->getCalibrationCoefficientsAll();
	print_array("VIS WL COEFFS", hs->cal_coefs.vnir_wavelength_coefficients, 6);
	print_array("VIS LIN COEFFS", hs->cal_coefs.vnir_linearity_coefficients, 8);
	print_array("SWIR WL COEFFS", hs->cal_coefs.swir_wavelength_coefs, 5);
	print_array("ACCEL REF", hs->cal_coefs.accelerometer_horizontal_reference, 3);

	std::cout << "SN: " << hs->ext_cal_coefs.instrument_serial_number << "\n";
	std::cout << "CAL DATE:" << hs->ext_cal_coefs.calibration_year << "-" << hs->ext_cal_coefs.calibration_month << "-" << hs->ext_cal_coefs.calibration_day << "\n";
	print_array("ACEL REF AGAIN" , hs->ext_cal_coefs.accelerometer_horizontal_reference, 3);
	print_array("VNIR NL coefs", hs->ext_cal_coefs.vnir_nonlinearity_coefficients, 4);
	print_array("VNIR coefs L", hs->ext_cal_coefs.vnir_coefficients_L, 2048);
	print_array("VNIR coefs E", hs->ext_cal_coefs.vnir_coefficients_E, 2048);
	print_array("SWIR NL coefs", hs->ext_cal_coefs.swir_nonlinearity_coefficients, 9);
	print_array("SWIR coefs L", hs->ext_cal_coefs.swir_coefficients_L, 256);
	print_array("SWIR coefs E", hs->ext_cal_coefs.swir_coefficients_E, 256);
	std::cout << "CRC32: " << hs->ext_cal_coefs.crc32 << "\n";
	delete hs;
	printf("\n------ \nC++ Test pass\n ------\n");


	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	s_calibration_coefficients_unpacked cal_coefs;
	s_extended_calibration_coefficients ext_coefs;
	if (hypstar_get_calibration_coefficients_basic(pHs, &cal_coefs))
	{
		printf("Got basic\n");
	}
	else
	{
		hypstar_close(pHs);
		return 1;
	}
	if (hypstar_get_calibration_coefficients_extended(pHs, &ext_coefs))
	{
		printf("Got extended\n");
	}
	else
	{
		hypstar_close(pHs);
		return 1;
	}
	if (hypstar_get_calibration_coefficients_all(pHs, &cal_coefs, &ext_coefs))
	{
		printf("Got both\n");
	}
	else
	{
		hypstar_close(pHs);
		return 1;
	}

	printf("--------------\nC Test pass\n");
	return 0;
}
