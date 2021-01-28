#include <iostream>

#include "../inc/hypstar.h"
#include <assert.h>

using namespace std;

void fill_cal_coef_struct(s_extended_calibration_coefficients *s);
void test_returned_struct_content(s_extended_calibration_coefficients *a, s_extended_calibration_coefficients *b);
int main() {
	std::string port = "/dev/ttyUSB0";
	s_extended_calibration_coefficients out;
	fill_cal_coef_struct(&out);

	printf("Cal date in C++test: %d-%d-%d\n", out.calibration_year, out.calibration_month, out.calibration_day);

	Hypstar *hs;
	hs = Hypstar::getInstance(port);
//	hs->setLoglevel(TRACE);
	hs->setLoglevel(DEBUG);

	hs->enterFlashWriteMode();
	hs->sendCalibrationCoefficients(&out);
	hs->saveCalibrationCoefficients();
	hs->reboot();
	hs->getCalibrationCoefficientsExtended();
	test_returned_struct_content(&hs->extended_calibration_coefficients, &out);
	printf("\n------ \nC++ Test pass\n ------\n");

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	out.calibration_day = out.calibration_day -1;
	printf("Cal date in C test: %d-%d-%d\n", out.calibration_year, out.calibration_month, out.calibration_day);
	hypstar_enter_flash_write_mode(pHs);
	hypstar_send_calibration_coefficients(pHs, &out);
	hypstar_save_calibration_coefficients(pHs);
	hypstar_reboot(pHs);
	s_extended_calibration_coefficients return_target;
	hypstar_get_calibration_coefficients_extended(pHs, &return_target);
	test_returned_struct_content(&return_target, &out);
	printf("--------------\nC Test pass\n");
	return 0;
}

void fill_cal_coef_struct(s_extended_calibration_coefficients *s)
{
	time_t now = time(NULL);
	auto *tm = localtime(&now);

	struct s_arr_item {
		int len;
		float *arr;
	};
	s_extended_calibration_coefficients out = *s;
	s->instrument_serial_number = 123456;
	s->calibration_year = tm->tm_year+1900;
	s->calibration_month = tm->tm_mon+1;
	s->calibration_day = tm->tm_mday;
	s->accelerometer_horizontal_reference[0] = 3648;
	s->accelerometer_horizontal_reference[1] = -192;
	s->accelerometer_horizontal_reference[2] = 15620;

	s->crc32 = 0;

	float vnir_nl_coefs[4], vnir_coefs_L[2048], vnir_coefs_E[2048], swir_nl_coefs[9], swir_coefs_L[256], swir_coefs_E[256];
	s_arr_item coefs[] = {
			{4,  s->vnir_nonlinearity_coefficients},
			{2048,  s->vnir_coefficients_L},
			{2048, s->vnir_coefficients_E},
			{9, s->swir_nonlinearity_coefficients},
			{256, s->swir_coefficients_L},
			{256, s->swir_coefficients_E},
	};
	for(int i = 0; i < sizeof(coefs)/sizeof(coefs[0]); i++)
	{
		for (int j = 0; j < coefs[i].len; j++)
		{
			coefs[i].arr[j] = i * 2 + (float)j / 10;
		}
	}
}

void test_returned_struct_content(s_extended_calibration_coefficients *a, s_extended_calibration_coefficients *b)
{
	char * a_char = (char*)a;
	char * b_char = (char*)b;

	for (int i = 0; i < sizeof(s_extended_calibration_coefficients); i++) {
		assert(a_char[i] == b_char[i]);
	}
}
