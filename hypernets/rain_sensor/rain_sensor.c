#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <getopt.h>
#include <sys/io.h>

/* Cincoze DE-1000 has Super I/O chip F81866A
*  Digital Inputs are GPIO74...GPIO77
*  Digital Outputs are GPIO80...GPIO83
*  Rain sensor is connected to first DI GPIO74
*  GPIO access is based on sample code in DE-1000 manual */

#define ExtModeON  0x87
#define ExtModeOFF 0xAA

#define AddrPort   0x4E
#define DataPort   0x4F

#define RainSensorMask 0b00010000

// return codes
#define RAINING 1
#define NOT_RAINING 0
#define ERROR 255

int check_gpio_access(int debug);
void configure_gpio_port(int debug);
unsigned char read_value(int debug);
void release_gpio_port(int debug);

// Print text to stdout if no parameters
// Print 0 or 1 to stdout if any parameter given
int main(int argc, char *argv[])
{
  int i_tmp;
  int debug = 0;
  int value = 0;

  // parse command line options
  while((i_tmp = getopt(argc, argv, "d")) != -1)
  {
    switch(i_tmp)
    {
    case 'd':
      debug = 1;
      break;
    }
  }

  if(check_gpio_access(debug))
  {
    if(debug)
	    fprintf(stderr, "[ERROR]  Failed to access rain sensor GPIO port\n");
    return ERROR;
  }

  configure_gpio_port(debug);

  value = read_value(debug);
  release_gpio_port(debug);

  if(value)
  {
  	if (debug)
  	  fprintf(stderr, "[DEBUG]  Rain is detected\n");

	return RAINING;
  }
  else
  {
  	if (debug)
      fprintf(stdout, "[DEBUG]  No Rain is detected\n");

	return NOT_RAINING;
  }

  // we should never reach here
  return ERROR;
}


int check_gpio_access(int debug)
{
  if (debug)
    fprintf(stderr, "[DEBUG]  Checking rain sensor GPIO access permissions\n");

  if(ioperm(AddrPort,(unsigned long) 3, 1) +
      ioperm(DataPort,(unsigned long) 3, 1) < 0)
  {
    return -1;
  }

  return 0;
}


void configure_gpio_port(int debug)
{
  if (debug)
    fprintf(stderr, "[DEBUG]  Configuring rain sensor GPIO port\n");

  /* Enter extended mode */
  outb(ExtModeON, AddrPort);
  outb(ExtModeON, AddrPort);	// must write twice

  /* Select Logic Device 06h */
  outb(0x07, AddrPort);
  outb(0x06, DataPort);

  /* Input Mode Selection for GP 74~77 
     and set(bit 4~7) = 0 to select  */

  outb(0x80, AddrPort);	// Select configuration register 80h
  outb(0x00, DataPort);
}


void release_gpio_port(int debug)
{
  if (debug)
    fprintf(stderr, "[DEBUG]  Releasing rain sensor GPIO port\n");

  outb(ExtModeOFF, AddrPort);	// Leave the Extended Funcion Mode
}


// return 0 if not raining and 1 if raining
unsigned char read_value(int debug)
{
  unsigned char value;
  outb(0x82, AddrPort);
  value = inb(DataPort);

  if (debug)
    fprintf(stderr, "[DEBUG]  Read 0x%.2X from GPIO port, masked rain sensor value is 0x%.2X\n", value, value & RainSensorMask);

  return value & RainSensorMask ? 1 : 0;
}
