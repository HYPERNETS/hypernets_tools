#include <iostream>
#include <assert.h>
#include "../inc/hypstar.h"
#include <ctime>
#include "common_functions.c"

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB0";
	Hypstar *hs = Hypstar::getInstance(port);
//	hs->setLoglevel(TRACE);
	hs->setLoglevel(DEBUG);

	std::cout << "Testing VIS RAD auto" << std::endl;
	int last_it = test_spec(hs, VNIR, RADIANCE, 0, 0, 1);

	std::cout << "Testing VIS IRRAD auto" << std::endl;
	last_it = test_spec(hs, VNIR, IRRADIANCE, 0, 0, 1);

	std::cout << "Testing VIS DARK auto" << std::endl;
	int latest_it = test_spec(hs, VNIR, DARK, 0, 0, 1);
	assert (last_it == last_it);

	if (hs->available_hardware.swir_module)
	{
		std::cout << "Testing SWIR RAD auto" << std::endl;
		test_spec(hs, SWIR, RADIANCE, 0, 0, 3);

		std::cout << "Testing BOTH IRRAD auto" << std::endl;
		test_spec(hs, BOTH, IRRADIANCE, 0, 0, 2);

		std::cout << "Testing BOTH DARK auto" << std::endl;
		test_spec(hs, BOTH, DARK, 0, 0, 1);
	}
	else
	{
		// should not segfault
		int r = hs->captureSpectra(SWIR, RADIANCE, 0, 0, 1, 0);
		assert (r == 0);
		printf("Got 0 spectra as expected\n");
	}

	// @TODO: test incorrect input params, that should get blocked by the driver
	// @TODO: acceleration == 0 for ITs lower than accelerometer refresh rate?
	printf("--------------\nC++ Test pass\n");

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
//	hypstar_set_loglevel(pHs, TRACE);
	hypstar_set_loglevel(pHs, DEBUG);
	int count = hypstar_capture_spectra(pHs, VNIR, RADIANCE, 0, 0, 2, 10);
	assert(count == 2);
	unsigned short slots[10];
	count = hypstar_get_last_capture_memory_slots(pHs, slots, count);
	assert(count == 2);
	assert(slots[0] > 1);
	s_spectrum_dataset spec_data[count];
	count = hypstar_download_spectra(pHs, slots, count, spec_data);
	assert(count == 2);
	assert(spec_data[0].spectrum_header.spectrum_config.radiance);
	assert(!spec_data[0].spectrum_header.spectrum_config.irradiance);
	assert(!spec_data[0].spectrum_header.spectrum_config.swir);
	assert(spec_data[0].spectrum_header.pixel_count == 2048);

	hypstar_close(pHs);
	printf("--------------\nC Test pass\n");
}
