#include <iostream>
#include <assert.h>
#include "../inc/hypstar.h"
#include <ctime>
#include <iomanip>
#include "common_functions.c"


int main() {
	std::string port = "/dev/ttyUSB0";
	Hypstar *hs = Hypstar::getInstance(port);
//	hs->setLoglevel(TRACE);
	hs->setLoglevel(DEBUG);

	std::cout << "Testing VIS RAD 100ms" << std::endl;
	test_spec(hs, VNIR, RADIANCE, 100, 0, 1);

	std::cout << "Testing VIS IRRAD 200ms" << std::endl;
	test_spec(hs, VNIR, IRRADIANCE, 200, 0, 1);

	std::cout << "Testing VIS DARK 10ms" << std::endl;
	test_spec(hs, VNIR, DARK, 50, 0, 10);

	if (hs->available_hardware.swir_module)
	{
		std::cout << "Testing SWIR RAD 300ms" << std::endl;
		test_spec(hs, SWIR, RADIANCE, 0, 65000, 1);
		std::cout << "Testing BOTH IRRAD 100ms" << std::endl;
		test_spec(hs, BOTH, IRRADIANCE, 100, 100, 2);
	}
	else
	{
		// should not segfault
		int r = hs->captureSpectra(SWIR, RADIANCE, 0, 100, 1, 0);
		assert (r == 0);
	}
	// @TODO: acceleration == 0 for ITs lower than accelerometer refresh rate?
	// @TODO: test incorrect input params, that should get blocked by the driver

	printf("--------------\nC++ Test pass\n");

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	hypstar_set_loglevel(pHs, DEBUG);
	int count = hypstar_capture_spectra(pHs, VNIR, RADIANCE, 100, 0, 2, 1);
	assert(count == 2);
	unsigned short slots[10];
	count = hypstar_get_last_capture_memory_slots(pHs, slots, count);
	assert(count == 2);
	assert(slots[0] > 1);
	s_spectrum_dataset spec_data[count];
	count = hypstar_download_spectra(pHs, slots, count, spec_data);
	assert(count == 2);
	assert(spec_data[0].spectrum_header.integration_time_ms == 100);
	assert(spec_data[0].spectrum_header.spectrum_config.radiance);
	assert(!spec_data[0].spectrum_header.spectrum_config.irradiance);
	assert(!spec_data[0].spectrum_header.spectrum_config.swir);
	assert(spec_data[0].spectrum_header.pixel_count == 2048);

	hypstar_close(pHs);
	printf("--------------\nC Test pass\n");
}
