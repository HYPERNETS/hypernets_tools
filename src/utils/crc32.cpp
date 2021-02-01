#include <stdio.h>
#include "crc32.h"

unsigned int crcTable[256];

unsigned char reflect8(unsigned char val)
{
    unsigned char resVal = 0;

    for (int i = 0; i < 8; i++)
    {
        if ((val & (1 << i)) != 0)
        {
            resVal |= (unsigned char)(1 << (7 - i));
        }
    }

    return resVal;
}


unsigned int reflect32(unsigned int val)
{
    unsigned int resVal = 0;

    for (int i = 0; i < 32; i++)
    {
        if ((val & (1 << i)) != 0)
        {
            resVal |= (unsigned int)(1 << (31 - i));
        }
    }

    return resVal;
}


void CalculateCrcTable_CRC32()
{
    const unsigned int polynomial = CRC32_POLYNOMIAL;

    for (int dividend = 0; dividend < 256; dividend++) /* iterate over all possible input byte values 0 - 255 */
    {
        unsigned int curByte = (unsigned int)(dividend << 24); /* move divident byte into MSB of 32Bit CRC */
        for (unsigned char bit = 0; bit < 8; bit++)
        {
            if ((curByte & 0x80000000) != 0)
            {
                curByte <<= 1;
                curByte ^= polynomial;
            }
            else
            {
                curByte <<= 1;
            }
        }

        crcTable[dividend] = curByte;
    }
}


unsigned int Compute_CRC32(unsigned long ulCount, unsigned char *message)
{
    unsigned int crc = 0xFFFFFFFF; /* CRC is set to specified initial value */
	unsigned long i;
	unsigned char curByte;
	unsigned char pos;

	for (i = 0; i <  ulCount; i++)
    {
        /* reflect input byte if specified, otherwise input byte is taken as it is */
        curByte = (CRC32_INPUT_REFL ? reflect8(message[i]) : message[i]);

        /* XOR-in next input byte into MSB of crc and get this MSB, that's our new intermediate divident */
        pos = (unsigned char)((crc ^ (curByte << 24)) >> 24);

        /* Shift out the MSB used for division per lookuptable and XOR with the remainder */
        crc = (unsigned int)((crc << 8) ^ (unsigned int)(crcTable[pos]));

//		printf("i=%lu, curByte=0x%.2X, pos=0x%.2X, crc=0x%.8X\n", i, curByte, pos, crc);
    }
	/* reflect result crc if specified, otherwise calculated crc value is taken as it is */
	crc = (CRC32_OUTPUT_REFL ? reflect32(crc) : crc);
    return (unsigned int)(crc ^ CRC32_FINAL_XOR);
}


// compute on big-endian data
unsigned int Compute_CRC32_BE(unsigned long ulCount, unsigned char *message)
{
    unsigned int crc = 0xFFFFFFFF; /* CRC is set to specified initial value */
	unsigned long i;
	unsigned char curByte;
	unsigned char pos;
	int j;

	if (ulCount % 4)
	{
		fprintf(stderr, "CRC32 must be calculated on buffer containing full 32-bit words\n");
		return 0;
	}

	// loop over 32-bit words instead of bytes
	for (i = 0; i < (ulCount >> 2); i++)
    {
		// loop over bytes inside the word in little-endian order
		for (j = 3; j >= 0; j--)
		{
			/* reflect input byte if specified, otherwise input byte is taken as it is */
			curByte = (CRC32_INPUT_REFL ? reflect8(message[(i << 2) + j]) : message[(i << 2) + j]);

			/* XOR-in next input byte into MSB of crc and get this MSB, that's our new intermediate divident */
			pos = (unsigned char)((crc ^ (curByte << 24)) >> 24);
			/* Shift out the MSB used for division per lookuptable and XOR with the remainder */
			crc = (unsigned int)((crc << 8) ^ (unsigned int)(crcTable[pos]));

//			printf("i=%lu, j=%d, curByte=0x%.2X, pos=0x%.2X, crc=0x%.8X\n", i, j, curByte, pos, crc);
		}
    }
	/* reflect result crc if specified, otherwise calculated crc value is taken as it is */
	crc = (CRC32_OUTPUT_REFL ? reflect32(crc) : crc);

#ifdef DEBUG
	fprintf(stderr, "Calculated CRC32 on %lu-byte buffer: 0x%.8X\n", ulCount, (unsigned int)(crc ^ CRC32_FINAL_XOR));
#endif

    return (unsigned int)(crc ^ CRC32_FINAL_XOR);
}
