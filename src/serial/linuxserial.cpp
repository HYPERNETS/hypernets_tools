/* linuxserial.cpp                  (C) Joel Kuusk, 2003-2014
 *
 * Communication with serial port
 */

#include <math.h>
#include <errno.h>
#include <strings.h>
#include <linux/serial.h>
#include <sys/ioctl.h>
#include "linuxserial.h"
#include "linuxserial_baudrate.h"

#include <sys/io.h>

using namespace LibHypstar;

linuxserial::linuxserial(int baud, const char* port)
{
	unsigned short baudrate;
	struct termios newtio;
	struct serial_struct ser_info;

	switch(baud) {
		case 460800: baudrate = B460800; break;
		case 500000: baudrate = B500000; break;
		case 115200: baudrate = B115200; break;
		case 230400: baudrate = B230400; break;
		case 57600: baudrate = B57600; break;
		case 38400: baudrate = B38400; break;
		case 9600: baudrate = B9600; break;
		case 4800: baudrate = B4800; break;
		case 2400: baudrate = B2400; break;
		case 1200: baudrate = B1200; break;
		case 600: baudrate = B600; break;
		case 300: baudrate = B300; break;
		default: baudrate = B9600; break;
	}

    // read will return immediately and it is a tty
	fd = open(port, O_RDWR | O_NOCTTY | O_NONBLOCK);

	if(fd < 0)
	{
		perror(port);
		fprintf(stderr, "\n%s: serial port open failed.\n",
			__PRETTY_FUNCTION__);
		throw eSerialOpenFailed();
	}

	bzero(&newtio, sizeof(newtio));
	newtio.c_cflag = baudrate | CS8 | CLOCAL | CREAD;
	newtio.c_iflag = IGNBRK | IGNPAR;
	newtio.c_oflag = 0;
	newtio.c_lflag = 0;
	newtio.c_cc[VMIN] = 0;
	newtio.c_cc[VTIME] = 0;
	tcflush(fd,TCIFLUSH);
	tcsetattr(fd, TCSANOW, &newtio);

	// Linux-specific: enable low latency mode (1 ms instead of FTDI default 16 ms)
	// equivalent to
	// echo 1 > /sys/bus/usb-serial/devices/ttyUSB0/latency_timer
	ioctl(fd, TIOCGSERIAL, &ser_info);
	ser_info.flags |= ASYNC_LOW_LATENCY;
	ioctl(fd, TIOCSSERIAL, &ser_info);

	emptyInputBuf();
}


void linuxserial::setBaud(int baud)
{
	if (!switchNonStandardBaudRate(fd, baud))
		throw eSerialError();
}


linuxserial::~linuxserial(void)
{
	if (fd >= 0)
	{
		tcdrain(fd);
		close(fd);
	}
}


int linuxserial::serialRead(unsigned char* buf, unsigned short count, float timeout_sec)
{
	int n;

	// set timeout
	readtimeout.tv_sec = (int)floor(timeout_sec);
	readtimeout.tv_usec = (int)((timeout_sec - readtimeout.tv_sec) * 1e6);

    // set up input descriptor
	FD_ZERO(&input);
	FD_SET(fd, &input);

	n = select(fd + 1, &input, NULL, NULL, &readtimeout);

    // select failed, some serious error must have occurred
	if (n < 0)
	{
		//select was interrupted by signal, e.g. ctrl-C
		if (errno == EINTR)
			throw eSerialSelectInterrupted();

		perror("linuxserial::serialRead: select");
		throw eSerialSelectError();
	}
    // timeout
	else if (n == 0)
	{
#ifdef DEBUG
		fprintf(stderr, "eSerialReadTimeout\n");
#endif
		throw eSerialReadTimeout();
	}
    // data in receive buffer
	else
	{
		n = read(fd, buf, count);

#ifdef DEBUG
		fprintf(stderr, "Rx: ");
		for (int i = 0; i < n; i++)
			fprintf(stderr, "%.2X ", buf[i]);
		fprintf(stderr, "\n");
#endif
	}

	return n;
}


unsigned char linuxserial::serialRead(float timeout_sec)
{
	unsigned char c;
	serialRead(&c, 1, timeout_sec);

	return c;
}


// Empty serial port's receive buffer
void linuxserial::emptyInputBuf(void)
{
	//sleep for 1.1 ms before flushing
	usleep(1100);
	tcflush(fd, TCIFLUSH);
}


void linuxserial::serialWrite(unsigned char* buf, unsigned short count, float timeout_sec)
{
	int n;

    // repeat until all data is transferred
	while (count > 0)
	{
        // set timeout (we must reset it after every select() call)
		writetimeout.tv_sec = (int)floor(timeout_sec);
		writetimeout.tv_usec = (int)((timeout_sec - writetimeout.tv_sec) * 1e6);

        // set up output descriptor
		FD_ZERO(&output);
		FD_SET(fd, &output);

		n = select(fd + 1, NULL, &output, NULL, &writetimeout);

        // select failed, some serious error must have occurred
		if (n < 0)
		{
			perror("select");
			throw eSerialSelectError();
		}
        // timeout
		else if (n == 0)
		{
			fprintf(stderr, "\n%s: could not write to serial port for %.1f seconds.\n",
				__PRETTY_FUNCTION__, timeout_sec);
			throw eSerialWriteTimeout();
		}
        // transmit buffer is empty
		else
		{
			n = write(fd, buf, count);

			if (n < 1)
			{
				perror("write");
				throw eSerialError();
			}

#ifdef DEBUG
			fprintf(stderr, "Tx, count = %d, n = %d\nTx: ", count, n);
			for (int i = 0; i < n; i++)
				fprintf(stderr, "%.2X ", buf[i]);
			fprintf(stderr, "\n");
#endif
			count -= n;
			buf += n;
		}
	}
}


void linuxserial::serialWrite(unsigned char c, float timeout_sec)
{
	serialWrite(&c, 1, timeout_sec);
}
