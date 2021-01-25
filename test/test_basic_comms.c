#include <iostream>
#include <assert.h>
#include "../inc/hypstar.h"

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB1";
	Hypstar *hs = Hypstar::getInstance(port);
	// test double inits
	Hypstar *hs_copy = Hypstar::getInstance(port);
	assert (hs == hs_copy);

	hs->setLoglevel(DEBUG);

	hs->setBaudRate(B_3000000);

	uint32_t sn = hs->hw_info.instrument_serial_number;
	printf("Instrument SN: %d\n", hs->hw_info.instrument_serial_number);
	printf("FW version: %d.%d.%d\n", hs->hw_info.firmware_version_major, hs->hw_info.firmware_version_minor, hs->hw_info.firmware_version_revision);
	printf("HW versions - PSU: %d, MCU: %d\n", hs->hw_info.psu_hardware_version, hs->hw_info.mcu_hardware_version);
	printf("VIS SN: %d\n", hs->hw_info.vis_serial_number);
	printf("SWIR SN: %d\n", hs->hw_info.swir_serial_number);
	printf("Memory slot count: %d\n", hs->hw_info.memory_slot_count);

	// test destructor resetting BR
	delete hs;

	printf("Trying 2rd invocation, should succeed\n");
	Hypstar *hs2 = Hypstar::getInstance(port);
	printf("Success\n");
	delete hs2;

	printf("--------------\nC++ Test pass\n");

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	hypstar_set_loglevel(pHs, DEBUG);
	s_booted boot_info_struct;
	hypstar_get_hw_info(pHs, &boot_info_struct);
	assert (sn == boot_info_struct.instrument_serial_number);
	hypstar_close(pHs);
	printf("Instrument SN: %d\n", boot_info_struct.instrument_serial_number);
	printf("FW version: %d.%d.%d\n", boot_info_struct.firmware_version_major, boot_info_struct.firmware_version_minor, boot_info_struct.firmware_version_revision);
	printf("HW versions - PSU: %d, MCU: %d\n", boot_info_struct.psu_hardware_version, boot_info_struct.mcu_hardware_version);
	printf("VIS SN: %d\n", boot_info_struct.vis_serial_number);
	printf("SWIR SN: %d\n", boot_info_struct.swir_serial_number);
	printf("Memory slot count: %d\n", boot_info_struct.memory_slot_count);

	// change baudrate
	pHs = hypstar_init(port.c_str());
	hypstar_set_baudrate(pHs, B_3000000);
	hypstar_get_hw_info(pHs, &boot_info_struct);
	hypstar_close(pHs);
	// check that baud rate has been reset to default 115200 after reinit
	pHs = hypstar_init(port.c_str());
	hypstar_get_hw_info(pHs, &boot_info_struct);
	hypstar_close(pHs);

	// test double inits
	pHs = hypstar_init(port.c_str());
	pHs = hypstar_init(port.c_str());
	hypstar_close(pHs);
	printf("--------------\nC test pass\n");

	return 0;
}
