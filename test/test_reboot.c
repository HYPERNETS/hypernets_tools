#include <iostream>

#include "../inc/hypstar.h"
#include <assert.h>
#include <chrono>

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB1";
	Hypstar *hs = Hypstar::getInstance(port);
	auto t1 = std::chrono::high_resolution_clock::now();
	hs->reboot();
	auto t2 = std::chrono::high_resolution_clock::now();
	auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
	printf("--------------\nC++ test pass, reboot took %.2f s\n", (float)duration/1000);

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	hypstar_set_loglevel(pHs, TRACE);
	t1 = std::chrono::high_resolution_clock::now();
	hypstar_reboot(pHs);
	t2 = std::chrono::high_resolution_clock::now();
	duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
	hypstar_close(pHs);
	printf("--------------\nC++ test pass, reboot took %.2f s\n", (float)duration/1000);
}
