#ifndef __CRC32_H
#define __CRC32_H

#define CRC32_INIT 0xFFFFFFFF
#define CRC32_POLYNOMIAL 0x04C11DB7L
#define CRC32_FINAL_XOR 0x00
#define CRC32_INPUT_REFL 0
#define CRC32_OUTPUT_REFL 0

extern unsigned int crcTable[256];

void CalculateCrcTable_CRC32();
unsigned int Compute_CRC32(unsigned long ulCount, unsigned char *message);
unsigned int Compute_CRC32_BE(unsigned long ulCount, unsigned char *message);

#endif // __CRC32_H
