#include <iostream>

#include "../inc/hypstar.h"
#include <assert.h>
#include <chrono>

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB0";
	Hypstar *hs = Hypstar::getInstance(port);
	hs->setLoglevel(TRACE);
	hs->setLoglevel(DEBUG);

	hs->getFirmwareInfo();
	int previousFwSlot = hs->firmware_info.current_flash_slot;
	printf("Current FW version: %d.%d.%d in slot %d\n", hs->firmware_info.firmware_version_major,
			hs->firmware_info.firmware_version_minor, hs->firmware_info.firmware_version_revision, hs->firmware_info.current_flash_slot);

	hs->sendNewFirmwareData("~/wrk/hypernets-pub/trunk/fw_updater/firmware/mm_fw_0_13_5.bin");
	hs->saveNewFirmwareData();
	hs->switchFirmwareSlot();

	hs->getFirmwareInfo();
	printf("New FW version: %d.%d.%d in slot %d\n", hs->firmware_info.firmware_version_major,
				hs->firmware_info.firmware_version_minor, hs->firmware_info.firmware_version_revision, hs->firmware_info.current_flash_slot);

	printf("--------------\nC++ test pass\n");
}
