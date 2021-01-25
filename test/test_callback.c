#include <iostream>

#include "../inc/hypstar.h"
#include <assert.h>

using namespace std;

void cb_fn(s_autoint_status *s)
{
	printf("Got call with params %d and %d\n", s->this_inttme_ms, s->next_inttme_ms);
}

int main() {
	hypstar_test_callback(NULL, cb_fn, 1, 2);
	printf("C test pass\n");
}
