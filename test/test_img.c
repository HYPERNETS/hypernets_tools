#include <iostream>
#include <iomanip>
#include <fstream>
#include <chrono>
#include <time.h>
#include <assert.h>

#include "../inc/hypstar.h"

using namespace std;

int main() {
	std::string port = "/dev/ttyUSB1";
	Hypstar *hs = Hypstar::getInstance(port);
	hs->setLoglevel(DEBUG);
	hs->setLoglevel(TRACE);
//	hs->setBaudRate(B_6000000);

	s_img_data_holder *target_image = (s_img_data_holder*)malloc(sizeof(s_img_data_holder));
	char filename[40];
	struct tm *timenow;
	time_t now = time(NULL);
	timenow = gmtime(&now);
	unsigned int image_size = 0;
//
//	auto t1 = std::chrono::high_resolution_clock::now();
//	unsigned int image_size = hs->acquireJpegImage(false, true, true, target_image);
//	auto t2 = std::chrono::high_resolution_clock::now();
//
//	auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
//	float throughput = (float)image_size/((float)duration*1000)*(float)1024;
//	printf("Got %lu bytes in %ld ms (%f kBps = %f kbps)\n", image_size, duration, throughput, throughput*8);
//
//	assert(image_size == target_image->image_size);
//

//
//	if (image_size)
//	{
//		// save image
//		strftime(filename, sizeof(filename), "%Y-%m-%d_%H-%M-%S.jpeg", timenow);
//		printf("Filename: %s\n", filename);
//		std::ofstream outfile (filename, std::ofstream::binary);
//		outfile.write((const char *)target_image->image_data_jpeg.image_body, target_image->image_size);
//		outfile.close();
//	}
//	else
//	{
//		printf("Failed to capture image\n");
//		delete hs;
//	}

	printf("--------------\nC++ Test pass\n");

	hypstar_t *pHs;
	pHs = hypstar_init(port.c_str());
	hypstar_set_baudrate(pHs, B_6000000);
	// @TODO: first capture with AF on fails?
	image_size = hypstar_capture_JPEG_image(pHs, true, false, true);
	if (image_size)
	{
		image_size = hypstar_download_JPEG_image(pHs, target_image);
	}

	// save image
	if (image_size)
	{
		timenow = gmtime(&now);
		strftime(filename, sizeof(filename), "%Y-%m-%d_%H-%M-%S-2.jpeg", timenow);
		printf("Filename: %s\n", filename);
		std::ofstream outfile2(filename, std::ofstream::binary);
		outfile2.write((const char *)target_image->image_data_jpeg.image_body, target_image->image_size);
		outfile2.close();
	}
	else
	{
		printf("Failed to capture image\n");
	}
	free(target_image);
	hypstar_close(pHs);
	printf("--------------\nC Test pass\n");
}
