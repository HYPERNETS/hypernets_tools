#include <stdio.h>
#include <asm/termbits.h> //termios2
#include <sys/ioctl.h>
#include "linuxserial_baudrate.h"

bool switchNonStandardBaudRate(int fd, int baud)
{
	struct termios2 tio;

	if (ioctl(fd, TCGETS2, &tio) < 0)
	{
		perror("TCGETS2");
		fprintf(stderr, "\n%s: ioctl failed.\n", __PRETTY_FUNCTION__);
		return false;
	}

	tio.c_cflag &= ~CBAUD;
	tio.c_cflag |= BOTHER;
	tio.c_ispeed = baud;
	tio.c_ospeed = baud;

	if (ioctl(fd, TCSETS2, &tio) < 0)
	{
		perror("TCSETS2");
		fprintf(stderr, "\n%s: ioctl failed.\n", __PRETTY_FUNCTION__);
		return false;
	}

	return true;
}
