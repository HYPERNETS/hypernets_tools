#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

#include <sys/io.h>


#define ExtModeON  0x87
#define ExtModeOFF 0xAA

#define AddrPort   0x4E
#define DataPort   0x4F


void check_gpio_access();
void configure_gpio_port();
int read_value();
void release_gpio_port();


int main(int argc, char * argv[]){

	// if (iopl(3) < 0)
	// {
	// 	printf("Error : no root privileges.\n");
	//  	return -1;
	// }

	check_gpio_access();

	configure_gpio_port();

	int value = 0;
	value = read_value();

	release_gpio_port();

	if ( value == 1 )
		printf("Rain is detected\n");
	else
		printf("No Rain is detected\n");

	return 0;
}


void check_gpio_access(){
	// Best practice to use ioperm ?
	if ( ioperm( AddrPort, (unsigned long) 3, 1 ) + 
		 ioperm( DataPort, (unsigned long) 3, 1 ) < 0){
		printf("Error : no access to GPIO.\n");
		exit(1);
	}
}

void configure_gpio_port(){
	/* Enter extended mode */
	outb( ExtModeON, AddrPort ); 
	outb( ExtModeON, AddrPort ); // must write twice

	/* Select Logic Device 06h */
	outb( 0x07, AddrPort );
	outb( 0x06, DataPort ); 

	/* Input Mode Selection GP 74~77 as input mode */
	/* and set (bit 4~7) = 0 to select */
	outb( 0x80, AddrPort ); // Select configuration register 80h
	outb( 0x00, DataPort );
}

void release_gpio_port(){
	outb( ExtModeOFF, AddrPort ); // Leave the Extended Funcion Mode
}

int read_value(){
	outb( 0x82, AddrPort );    // read and shift right 4 times
	return inb(DataPort) >> 4; // to get a rid of bit 0~3 values
}
