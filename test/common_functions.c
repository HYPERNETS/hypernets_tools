using namespace std;

void test_and_print_single_spec(unsigned short slot, s_spectrum_dataset *s, int inttime_vis, int inttime_swir, e_radiometer rad, e_entrance entr)
{
	int pix_cnt_exp = 2048;
	int inttime_exp = inttime_vis;

	if (s->spectrum_header.spectrum_config.swir) {
		pix_cnt_exp = 256;
		inttime_exp = inttime_swir;
	}

	Spectrum sp = Spectrum(s);
	assert(s->spectrum_header.integration_time_ms == sp.integration_time);
	assert(s->spectrum_header.pixel_count == sp.pixel_count);
	if (s->spectrum_header.spectrum_config.swir) {
		assert (*(uint32_t*)&s->spectrum_body[256] == 0);
	}
	assert(s->crc32_spaceholder);

	char timebuff[100];
	time_t t = s->spectrum_header.timestamp_ms / 1000;
	auto tm = *localtime(&t);
	strftime(timebuff, sizeof(timebuff), "%Y-%m-%d %H:%M:%S", &tm);

	printf("\nSlot: %d\n", slot);
	printf("Timestmap: %ld (%s)\n", (long)s->spectrum_header.timestamp_ms, timebuff);
	printf("Radiance: %d, irradiance: %d\n", s->spectrum_header.spectrum_config.radiance, s->spectrum_header.spectrum_config.irradiance);
	printf("Entrances: VIS: %d, SWIR: %d\n", s->spectrum_header.spectrum_config.vnir, s->spectrum_header.spectrum_config.swir);
	printf("Integration time: %d ms\n", s->spectrum_header.integration_time_ms);
	printf("Pixel count: %d\n", s->spectrum_header.pixel_count);
	printf("Acceleration:\n");
	printf("\tX: %i +- %i\n",  s->spectrum_header.acceleration_statistics.X.mean_acceleration,  s->spectrum_header.acceleration_statistics.X.standard_deviation);
	printf("\tY: %i +- %i\n",  s->spectrum_header.acceleration_statistics.Y.mean_acceleration,  s->spectrum_header.acceleration_statistics.Y.standard_deviation);
	printf("\tZ: %i +- %i\n",  s->spectrum_header.acceleration_statistics.Z.mean_acceleration,  s->spectrum_header.acceleration_statistics.Z.standard_deviation);
	printf("Sensor temp: %.2f 'C\n", s->spectrum_header.sensor_temperature);
	printf("CRC32: 0x%08X\n", s->crc32_spaceholder);

	if (entr != DARK) {
		assert(s->spectrum_header.spectrum_config.radiance == (entr == RADIANCE));
		assert(s->spectrum_header.spectrum_config.irradiance == (entr == IRRADIANCE));
	}
	else
	{
		assert(!s->spectrum_header.spectrum_config.radiance);
		assert(!s->spectrum_header.spectrum_config.irradiance);
	}
	if (inttime_exp)
	{
		assert(s->spectrum_header.integration_time_ms == inttime_exp);
	}
}

int test_spec(Hypstar *hs, e_radiometer rad, e_entrance entr, int inttime_vis, int inttime_swir, int cap_count) {
	int count = hs->captureSpectra(rad, entr, inttime_vis, inttime_swir, cap_count, 0);
	if (rad == BOTH)
	{
		if (inttime_vis && inttime_swir) {
			cap_count = cap_count * 2;
		}
	}
//	assert(count == cap_count);
	unsigned short slots[count];
	hs->getLastSpectraCaptureMemorySlots(slots, count);
	s_spectrum_dataset specs[count];
	s_spectrum_dataset *s = &specs[0];

	int counter = 0;
	// test getting single
	printf("Slot single: %d\n", slots[counter]);
	hs->getSingleSpectrumFromMemorySlot(slots[counter], s);
	test_and_print_single_spec(slots[counter], s, inttime_vis, inttime_swir, rad, entr);

	// test getting many
	if (++counter < count)
	{
		hs->getSpectraFromMemorySlots(&slots[counter], count-1, &specs[counter]);
		do {
			s = &specs[counter];
			test_and_print_single_spec(slots[counter], s, inttime_vis, inttime_swir, rad, entr);
		} while (++counter < count);
	}
	return specs[0].spectrum_header.integration_time_ms;
}
