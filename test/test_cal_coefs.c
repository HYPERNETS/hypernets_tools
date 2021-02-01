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
	std::string port = "/dev/ttyUSB0";
	Hypstar *hs = Hypstar::getInstance(port);
	hs->setLoglevel(DEBUG);

	hs->getCalibrationCoefficientsAll();
	print_array("VIS WL COEFFS", hs->calibration_coefficients_basic.vnir_wavelength_coefficients, 6);
	print_array("VIS LIN COEFFS", hs->calibration_coefficients_basic.vnir_linearity_coefficients, 8);
	print_array("SWIR WL COEFFS", hs->calibration_coefficients_basic.swir_wavelength_coefs, 5);
	print_array("ACCEL REF", hs->calibration_coefficients_basic.accelerometer_horizontal_reference, 3);

	std::cout << "SN: " << hs->extended_calibration_coefficients.instrument_serial_number << "\n";
	std::cout << "CAL DATE:" << hs->extended_calibration_coefficients.calibration_year << "-" << hs->extended_calibration_coefficients.calibration_month << "-" << hs->extended_calibration_coefficients.calibration_day << "\n";
	print_array("ACEL REF AGAIN" , hs->extended_calibration_coefficients.accelerometer_horizontal_reference, 3);
//	print_array("VNIR NL coefs", hs->extended_calibration_coefficients.vnir_nonlinearity_coefficients, 4);
//	print_array("VNIR coefs L", hs->extended_calibration_coefficients.vnir_coefficients_L, 2048);
//	print_array("VNIR coefs E", hs->extended_calibration_coefficients.vnir_coefficients_E, 2048);
//	print_array("SWIR NL coefs", hs->extended_calibration_coefficients.swir_nonlinearity_coefficients, 9);
//	print_array("SWIR coefs L", hs->extended_calibration_coefficients.swir_coefficients_L, 256);
//	print_array("SWIR coefs E", hs->extended_calibration_coefficients.swir_coefficients_E, 256);
	std::cout << "CRC32: " << hs->extended_calibration_coefficients.crc32 << "\n";
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
