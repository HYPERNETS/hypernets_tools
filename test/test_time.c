#include <iostream>

#include "../inc/hypstar.h"
#include <assert.h>

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB1";
	Hypstar *hs = Hypstar::getInstance(port);
	hs->setLoglevel(TRACE);
	time_t timestamp = time(NULL);
	uint64_t ts_back = hs->getTime();
	// expect < 1s difference
	assert(ts_back < ((timestamp+1)*1000));
	assert(ts_back > (timestamp*1000));
	delete hs;
	printf("--------------\nC++ test pass, time read: %li ms, while current is %li s\n", ts_back, timestamp);

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	hypstar_set_loglevel(pHs, TRACE);
	timestamp = 1610368888;
	hypstar_set_time(pHs, timestamp);
	ts_back = hypstar_get_time(pHs);
	assert(ts_back < ((timestamp+1)*1000));
	assert(ts_back > (timestamp*1000));
	hypstar_close(pHs);
	printf("--------------\nC test pass, time read: %li\n", ts_back);
}
