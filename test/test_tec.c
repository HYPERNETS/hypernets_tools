#include <iostream>
#include <assert.h>
#include "../inc/hypstar.h"

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB1";
	Hypstar *hs = Hypstar::getInstance(port);
	hs->setLoglevel(TRACE);
	hs->setTECSetpoint(-7);

	printf("shutting down TEC and letting it warm up for 5s\n");
	hs->shutdown_TEC();

	sleep(5);

	printf("Now retrying\n");
	hs->setTECSetpoint(0);
	hs->shutdown_TEC();
	printf("--------------\nC++ Test pass\n");

	hypstar_t *pHs = hypstar_init(port.c_str());
	hypstar_set_TEC_target_temperature(pHs, 32.2);
	hypstar_shutdown_TEC(pHs);

	hypstar_close(pHs);
	printf("--------------\nC Test pass\n");

	return 0;
}
