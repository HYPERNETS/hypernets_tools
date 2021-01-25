#ifndef __LINUXSERIAL_H
#define __LINUXSERIAL_H

#include <string>    //string container, bzero()
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/types.h> // select()
#include <sys/time.h>  // select()
#include <sys/ioctl.h>

//#define COM3_PORT "/dev/ttyS2"
//#define COM4_PORT "/dev/ttyS3"
//#define COM5_PORT "/dev/COM5"
//#define COM6_PORT "/dev/COM6"
// udev rules:
//KERNEL=="ttyUSB[0-9]*", ATTRS{interface}=="Dual RS232-HS", ATTRS{bInterfaceNumber}=="00", SYMLINK="COM5", GROUP="tty", MODE="0660"
//KERNEL=="ttyUSB[0-9]*", ATTRS{interface}=="Dual RS232-HS", ATTRS{bInterfaceNumber}=="01", SYMLINK="COM6", GROUP="tty", MODE="0660"

#define READTIMEOUT 0.5
#define WRITETIMEOUT 0.5

// Exceptions
namespace LibHypstar {
	class eSerialError {};
	class eSerialWriteTimeout: public eSerialError {};
	class eSerialReadTimeout: public eSerialError {};
	class eSerialOpenFailed: public eSerialError {};
	class eSerialSelectError: public eSerialError {};
	class eSerialSelectInterrupted: public eSerialError {};

	class linuxserial
	{
	public:
		linuxserial(int baud, const char* port);
		~linuxserial(void);

		void setBaud(int baud);
		int serialRead(unsigned char* data, unsigned short len, float timeout_sec = READTIMEOUT);
		unsigned char serialRead(float timeout_sec = READTIMEOUT);
		void emptyInputBuf(void);
		void serialWrite(unsigned char* data, unsigned short len, float timeout_sec = WRITETIMEOUT);
		void serialWrite(unsigned char data, float timeout_sec = WRITETIMEOUT);

	private:
		int fd;
		fd_set input, output;
		struct timeval readtimeout, writetimeout;
	};
} // namespace LibHypstar

#endif /* __LINUXSERIAL_H */
