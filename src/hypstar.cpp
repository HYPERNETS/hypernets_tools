#include "../inc/hypstar.h"

#include "crc32.h"
#include <string.h>
#include <sstream>
#include <chrono>
#include <iomanip>
#include <math.h>
#include <iostream>
#include <fstream>

#define LOG(level, stream, format, ...) outputLog(level, #level, stream, format, ##__VA_ARGS__)
#define LOG_DEBUG(format, ...) LOG(DEBUG, stdout, format, ##__VA_ARGS__)
#define LOG_INFO(format, ...) LOG(INFO, stdout, format, ##__VA_ARGS__)
#define LOG_ERROR(format, ...) LOG(ERROR, stderr, format, ##__VA_ARGS__)
#define LOG_TRACE(format, ...) LOG(TRACE, stdout, format, ##__VA_ARGS__)

void Hypstar::outputLog(e_loglevel level, const char* level_string, FILE *stream, const char* fmt, ...)
{
	if (_loglevel >= level)
	{
		time_t now = time(NULL);
		auto tm = localtime(&now);
		char timebuf[22];
		strftime(timebuf, 20, "%Y-%m-%dT%H:%M:%S", tm);

		fprintf(stream, "[%s]\t[%s] ", level_string, timebuf);

		va_list args;
		va_start(args, fmt);
		vfprintf(stream, fmt, args);
		va_end(args);
	}
}

void Hypstar::logBinPacket(const char* direction, unsigned char* packet, int len)
{
	char out[len*3 +3];
	for (int i = 0; i < len; i++)
	{
		sprintf(&out[i*3], "%.2X ", packet[i]);
	}
	LOG_TRACE("%s %s\n", direction, out);
}

void Hypstar::logBytesRead(int rx_count, const char * expectedCommand, const char * cmd)
{
	char out[rx_count*3 +16];
	for (int i = 0; i < rx_count; i++)
	{
		sprintf(&out[i*3], "%.2X ", rxbuf[i]);
	}
	LOG_ERROR("Did not receive %s for command %.2X in %d attempts\n", expectedCommand, cmd, CMD_RETRY);
	LOG_ERROR("%d bytes read: %s\n", rx_count, out);
}

void Hypstar::setLoglevel(e_loglevel loglevel) {
	_loglevel = loglevel;
}

int Hypstar::findInstrumentBaudrate(int expectedBbaudrate)
{
	for (auto br : {B_115200, B_460800, B_921600, B_3000000, B_6000000, B_8000000})
	{
		LOG_ERROR("Trying baud rate %d\n", br);
		hnport->setBaud(br);
		try
		{
			while (true)
			{
				hnport->serialRead();
			}
		}
		catch (eSerialReadTimeout &e){}
		try
		{
			getHardWareInfo();
			return br;
		}
		catch (eBadTxCRC&)
		{
			// if we managed to unpack error, this is it
			return br;
		}
		catch (eHypstar&){}
	}
	return 0;
}

Hypstar::Hypstar(std::string portname)
{
	setLoglevel(INFO);

	try
	{
		LOG_INFO("Creating serial port (baud=%d, portname=%s)\n", DEFAULT_BAUD_RATE, portname.c_str());
		hnport = new linuxserial(DEFAULT_BAUD_RATE, portname.c_str());
	}
	catch (eSerialOpenFailed&)
	{
		LOG_ERROR("%s port open failed\n\n", portname.c_str());
		throw eHypstar();
	}

	LOG_DEBUG("Got serial port\n");

	// clear serial buffer
	try
	{
		while (true)
			hnport->serialRead();
	}
	catch (eSerialReadTimeout &e){}

	CalculateCrcTable_CRC32();

	try {
		getHardWareInfo();
	}
	catch (eBadInstrumentState&) {
		// we are in firmware upgrade mode, regular commands will fail now
//		throw eBadInstrumentState();
		return;
	}
	catch (eHypstar&)
	{
		LOG_ERROR("Did not get response from instrument, will try different baud rates\n");
		int response = findInstrumentBaudrate(DEFAULT_BAUD_RATE);
		LOG_ERROR("Got baud rate %d\n", response);
		if(!response)
		{
			throw eHypstar();
		}
	}

	// remap to proper bools for python
	available_hardware.vnir_module = hw_info.vnir_module_available;
	available_hardware.swir_module = hw_info.swir_module_available;
	available_hardware.optical_multiplexer = hw_info.optical_multiplexer_available;
	available_hardware.accelerometer = hw_info.accelerometer_available;
	available_hardware.camera = hw_info.camera_available;
	available_hardware.humidity_sensor = hw_info.humidity_sensor_available;
	available_hardware.pressure_sensor = hw_info.pressure_sensor_available;
	available_hardware.swir_tec_module = hw_info.swir_tec_module_available;

	setTime(time(NULL));
}

//destructor
Hypstar::~Hypstar()
{
	setBaudRate(B_115200);
	// destructor has to find and remove own entry from the instance_holder vector
	for (uint i = 0; i < Hypstar::instance_holder.size(); i++)
	{
		// if found, return pointer to that
		if (Hypstar::instance_holder[i].instance == this)
		{
			LOG_INFO("Found driver instance %p, index %d. Deleting...\n", static_cast<void*>(this), i);
			Hypstar::instance_holder.erase(Hypstar::instance_holder.begin()+i);
		}
	}
}

bool Hypstar::reboot(void)
{
	sendCmd(REBOOT);
	readData(15);
	return true;
}

bool Hypstar::sendCmd(unsigned char cmd, unsigned char* pPacketParams, unsigned short paramLength)
{
	// packet length 2 octets little endian cmd(1) + length(2) + payload(len) + crc(1)
	unsigned short txlen = paramLength + 4;

	// round up to multiple of 32bit words for crc calculation (w/o crc byte itself, thus -1)
	unsigned short crclen;
	crclen = ((txlen - 1) % 4) ? ((txlen - 1) + 4 - ((txlen - 1) % 4)) : (txlen - 1);

	unsigned short buflen = crclen > txlen ? crclen : txlen;
	unsigned char crcbuf[buflen];
	unsigned int crc; //CRC of command + parameters

	// clear buffer
	memset(crcbuf, 0, buflen);

	crcbuf[0] = cmd;
	// packet length 2 octets little endian cmd(1) + length(2) + payload(len) + crc(1)
	crcbuf[1] = txlen & 0xFF;
	crcbuf[2] = (txlen >> 8) & 0xFF;

	// copy optional parameters
	if (paramLength)
	{
		memcpy(crcbuf + 3, pPacketParams, paramLength);
	}

	//calculate CRC
	crc = Compute_CRC32_BE(crclen, crcbuf);
	crcbuf[txlen - 1] = crc & 0xFF;

	LOG_DEBUG("sendCmd, len=%d, txlen=%d, crclen=%d, buflen=%d, crc=0x%.8X\n", paramLength, txlen, crclen, buflen, crc);
	logBinPacket(">>", crcbuf, txlen);

	try
	{
		hnport->serialWrite(crcbuf, txlen);
	}
	catch(eSerialError &e)
	{
		LOG_ERROR("%s: could not send command to spectrometer\n", __PRETTY_FUNCTION__);
		return false;
	}

	return true;
}


// cmd - command token
// overloaded member function, provided for convenience
bool Hypstar::sendCmd(unsigned char cmd)
{
	return sendCmd(cmd, NULL, 0);
}


bool Hypstar::sendAndWaitForAcknowledge(unsigned char cmd, unsigned char* pPacketParams, unsigned short packetParamLength, const char* pCommandNameString)
{
	unsigned short receivedByteCount = 0;

	try
	{
		receivedByteCount = exchange(cmd, pPacketParams, packetParamLength, pCommandNameString);

		if ((rxbuf[0] != ACK) || (rxbuf[3] != cmd))
		{
			logBytesRead(receivedByteCount, "ACK", pCommandNameString);
			return false;
		}
		LOG_DEBUG("Got ACK for %s\n", pCommandNameString);
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("sendAckCmd failed with exception, cmd = %.2X\n", cmd);
		return false;
	}

	return true;
}


bool Hypstar::waitForDone(unsigned char cmd, const char* cmd_str, float timeout_s) {
	unsigned short receivedByteCount;
	int retryCount;

	// DONE
	for (retryCount = 0; retryCount < CMD_RETRY; retryCount++)
	{
		receivedByteCount = readData(timeout_s);

		if ((rxbuf[0] == DONE) && (rxbuf[3] == cmd))
		{
			LOG_DEBUG("Got DONE for %s\n", cmd_str);
			return true;
		}
	}

	if (retryCount == CMD_RETRY)
	{
		logBytesRead(receivedByteCount, "DONE", cmd_str);
		return false;
	}
	LOG_ERROR("NO DONE for %s\n", cmd_str);
	return false;
}

bool Hypstar::sendAndWaitForAckAndDone(unsigned char cmd, unsigned char* pPacketParams, unsigned short paramLength, const char* pCommandNameString, float timeout_s)
{
	sendAndWaitForAcknowledge(cmd, pPacketParams, paramLength, pCommandNameString);
	return waitForDone(cmd, pCommandNameString, timeout_s);
}

bool Hypstar::sendAndWaitForDone(unsigned char cmd, unsigned char* pPacketParams, unsigned short paramLength, const char* pCommandNameString, float timeout_s)
{
	sendCmd(cmd, pPacketParams, paramLength);
	return waitForDone(cmd, pCommandNameString, timeout_s);
}

//read data
int Hypstar::readData(float timeout_s)
{
	int count = 0;
	unsigned int i;
	bool good_id = false;
	unsigned short length = 0, crc_buflen, cmd_len = 0;
	unsigned char calc_crc, rx_crc, errcode;
	std::stringstream error_ss;

	LOG_DEBUG("readData timeout_sec = %.3f\n", timeout_s);
    auto t1 = std::chrono::high_resolution_clock::now();

	try
	{
		// read response code and packet length
		while (count < 3)
		{
			count += hnport->serialRead(rxbuf + count, 3 - count, timeout_s);
		}

		length = *((unsigned short*)(rxbuf + 1));

		while ((count < length) && (count < RX_BUFFER_PLUS_CRC32_SIZE))
		{
			count += hnport->serialRead(rxbuf + count, length - count, timeout_s);
		}
	}
	catch (eSerialReadTimeout &e){}
	catch (eSerialSelectInterrupted &e)
	{
		throw eHypstar();
	}

	auto t2 = std::chrono::high_resolution_clock::now();
	auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();

	LOG_DEBUG("Got %d bytes in %d ms\n", count, duration);
	logBinPacket("<<", rxbuf, count);

	if (count < 3)
	{
		LOG_ERROR("Received less than 3 bytes (%d)\n", count);
		throw eBadLength();
	}

	for (i = 0; i < (sizeof(packet_identifiers) / sizeof(packet_identifiers[0])); i++)
	{
		if(rxbuf[0] == packet_identifiers[i])
		{
			good_id = true;
			break;
		}
	}

	if (!good_id)
	{
		LOG_ERROR("Unknown packet identifier 0x%.2X\n", rxbuf[0]);
		throw eBadID();
	}

	if (count != length)
	{
		LOG_ERROR("Received %d bytes instead of %d bytes\n", count, length);
		throw eBadLength();
	}

	rx_crc = rxbuf[count - 1];

	crc_buflen = ((count - 1) % 4) ? (count - 1) + 4 - ((count - 1) % 4) : (count - 1);

	if (crc_buflen > RX_BUFFER_PLUS_CRC32_SIZE)
	{
		LOG_ERROR("Data buffer (len=%d) is too small for CRC calculation (required len=%d)\n", RX_BUFFER_PLUS_CRC32_SIZE, crc_buflen);
		throw eHypstar();
	}

	// pad with zeros if necessary (zero the crc byte too, hence -/+ 1)
	if (crc_buflen != (count - 1) && (crc_buflen <= RX_BUFFER_PLUS_CRC32_SIZE))
		memset(rxbuf + count - 1, 0, crc_buflen - (count - 1));

	//calculate CRC
	calc_crc = Compute_CRC32_BE(crc_buflen, rxbuf);
	if ((calc_crc & 0xFF) != rx_crc)
	{
		LOG_ERROR("Packet CRC (0x%.2X) does not match calculated CRC (0x%.2X)\n", rx_crc, calc_crc);
		throw eBadRxCRC();
	}

	// check response code
	if (rxbuf[0] == NAK)
	{
		// check for CRC error 0xE0 first
		// in the case of CRC error the packet received and returned by the instrument
		// is faulty and decoding it is meaningless
		if (rxbuf[count - 2] == BAD_CRC)
		{
			LOG_ERROR("Spectrometer responded with error 0x%.2X - bad crc\n", BAD_CRC);
			throw eBadTxCRC();
		}

		// check for too_short error 0xE4 next
		// in the case of too_short error the packet received and returned by the instrument
		// is shorter than declared in the header and decoding it is meaningless
		if (rxbuf[count - 2] == TOO_SHORT)
		{
			LOG_ERROR("Spectrometer responded with error 0x%.2X - too short\n", TOO_SHORT);
			throw eBadTxCRC();
		}

		// probably temporary fix to bug in fw that sends NOT_IMPLEMENTED back without
		// the original command
		// throw eBadTxCRC because the NOT_IMPLEMENTED error is occasionally
		// returned to command that is actually implemented (comms error with matching crc?)
		if (rxbuf[count - 2] == NOT_IMPLEMENTED)
		{
			LOG_ERROR("Spectrometer responded with error 0x%.2X - not implemented\n", NOT_IMPLEMENTED);
			throw eBadTxCRC();
		}

		// Response packet: response code(1), packet_length(2), cmd_code(1), cmd_packet_length(2), rest_of_cmd_packet(...), error_code(1)
		cmd_len = *((unsigned short*)(rxbuf + 4));

		// sanity check
		if ((3 + cmd_len) > (count - 1))
		{
			LOG_ERROR("Command length (%hu) in error packet is too long compared to received data length (%hu)\n", cmd_len, count);
			throw eBadRx();
		}

		errcode = rxbuf[3 + cmd_len];
		error_ss << "Spectrometer responded with error " << std::hex <<  (unsigned short)errcode << std::dec << " - ";

		// Response packet: response code(1), packet_length(2), cmd_code(1), cmd_packet_length(2), rest_of_cmd_packet(...), (n x {error_code(1), parm_no(1)}, crc(1)
		unsigned short n_errors = (length - 1 - 2 -  cmd_len - 1) / 2;
		unsigned short errcode2, parm2;

		switch(errcode)
		{
		case BAD_CRC:
			LOG_ERROR("bad crc\n");
			throw eBadTxCRC();
			break;
		case BAD_LENGTH:
			LOG_ERROR("bad length\n");
			break;
		case BAD_PARM:
			for (unsigned short j = 0; j < n_errors; j++)
			{
				errcode2 = rxbuf[3 + cmd_len + 1 + 2 * j];
				parm2 = rxbuf[3 + cmd_len + 1 + 2 * j + 1];

				switch(errcode2)
				{
				case PARM_OUT_OF_RANGE:
					error_ss << "Parameter " << parm2 << " error - out of range\n";
					break;
				case HW_NA:
					error_ss << "Parameter " << parm2 << " error - hardware not available\n";
					break;
				case WRONG_SPEC:
					error_ss << "Parameter " << parm2 << " error - wrong spectrometer selection, probably none active\n";
					break;
				case WRONG_OPTICS:
					error_ss << "Parameter " << parm2 << " error - wrong MUX setting, probably radiance and irradiance simultaneously\n";
					break;
				case NO_LIMIT:
					error_ss << "Parameter " << parm2 << " error - no limiting parameter has been provided (scan_count, series_time or DARK AUTO with no previous capture)\n";
					break;
				case INT_TOO_LONG:
					error_ss << "Parameter " << parm2 << " error - integration time too long\n";
					break;
				case SEQ_TOO_LONG:
					error_ss << "Parameter " << parm2 << " error - series time too long\n";
					break;
				case BAD_IMG_TYPE:
					error_ss << "Parameter " << parm2 << " error - bad image type code\n";
					break;
				case BAD_RESOLUTION:
					error_ss << "Parameter " << parm2 << " error - bad image resolution\n";
					break;

				default:
					error_ss << "Parameter " << parm2 << " error -  - unknown error "  << errcode2 << "\n";
					break;
				}
			}
			break;
		case TOO_SHORT:
			LOG_ERROR("too short\n");
			break;
		case NOT_IMPLEMENTED:
			LOG_ERROR("command 0x%.2X not implemented\n", rxbuf[3]);
			break;
		case BAD_STATE:
			LOG_ERROR("instrument is in firmware update mode\n");
			throw eBadInstrumentState();
			break;
		case MISSING_PARMS:
			LOG_ERROR("command too short to fill all the parameters\n");
			break;
		default:
			LOG_ERROR("unknown error code\n");
			break;
		}

		for (int i = 0; i < count; i++)
			error_ss << " " << std::hex << std::setfill('0') << std::uppercase << std::setw(2) << (unsigned short) rxbuf[i];

		LOG_ERROR("%s\n", error_ss.str().c_str());

		throw eBadResponse();
	}

	return count;
}

int Hypstar::exchange(unsigned char cmd, unsigned char* pPacketParams, unsigned short paramLength, const char* pCommandNameString, float timeout_s)
{
	int receivedByteCount = 0;
	bool resend = false;
	for (int i = 0; i < CMD_RETRY; i++)
	{
		try
		{
			if (resend)
			{
				LOG_DEBUG("%s: sendCmd(RESEND)\n", __PRETTY_FUNCTION__);
				hnport->emptyInputBuf();
				sendCmd(RESEND);
				resend = false;
			}
			else
			{
				LOG_DEBUG("%s: sendCmd(%s)\n", __PRETTY_FUNCTION__, pCommandNameString);
				sendCmd(cmd, pPacketParams, paramLength);
			}

			try
			{
				receivedByteCount = readData(timeout_s);
			}
			catch (eBadTxCRC &e)
			{
				// try again if instrument reported Tx crc error
				LOG_DEBUG("Instrument reported TX CRC error\n");
				continue;
			}
			catch (eBadRx &e)
			{
				// Resend if Rx crc error or too few bytes received
				LOG_DEBUG("Got garbage from instrument, requesting repeat\n");
				resend = true;
				continue;
			}
		}
		catch (eBadInstrumentState &e) {
			throw e;
		}
		catch (eHypstar &e)
		{
			LOG_ERROR("Failed to get %s packet\n", pCommandNameString);
			throw e;
		}

		break;
	}
	if (!receivedByteCount) {
		throw eHypstar();
	}
	return receivedByteCount;
}

int Hypstar::getPacketedData(char cmd, unsigned char * pPacketParams, unsigned short paramLength, unsigned char * pTargetMemory, const char * pCommandNameString)
{
	unsigned short packet_count = 0;
	unsigned short data_len = 0;
	int total_length = 0;
	unsigned char *dataset_tail = pTargetMemory;

	unsigned char param_holder[paramLength +sizeof(unsigned short)];
	unsigned short *packet_id = (unsigned short*)&param_holder[paramLength];
	*packet_id = 0;
	int packet_param_len = sizeof(param_holder);

	if (pPacketParams) {
		memcpy(param_holder, pPacketParams, paramLength);
	}

	do
	{
		LOG_DEBUG("packet=%hu/%hu, data_len=%hu\n", *packet_id + 1, packet_count, data_len);
		exchange(cmd, param_holder, packet_param_len, pCommandNameString);
		data_len = *((unsigned short*)(rxbuf + 1)) - 1 - 2 - 2 - 2 - 1;
		packet_count = *((unsigned short*)(rxbuf + 5));
		memcpy(dataset_tail, rxbuf + 7, data_len);
		dataset_tail += data_len;
		total_length += data_len;
	} while (++(*packet_id) < packet_count);

	// check crc of dataset
	// crc32 was last 4 bytes of payload
	unsigned int rx_crc32 = *(unsigned int*)(dataset_tail - 4);
	// clear provided CRC32, we might need to append 0x00 to match 32-bit boundaries
	// this is to avoid copying whole dataset around
	*(unsigned int*)(dataset_tail - 4) = 0;
	unsigned int crc32_buflen = ((total_length - 4) % 4) ?
			(total_length - 4) + 4 - ((total_length - 4) % 4) :
			(total_length - 4);
	unsigned int calc_crc32 = Compute_CRC32_BE(crc32_buflen, (unsigned char*)pTargetMemory);

	// put back CRC32
	*(unsigned int*)(dataset_tail - 4) = rx_crc32;

	LOG_DEBUG("Dataset total length=%d, crc32_buflen=%d, calc_crc32=0x%.8X, rx_crc32=0x%.8X\n",
					total_length, crc32_buflen, calc_crc32, rx_crc32);


	if (calc_crc32 != rx_crc32) {
		/* @TODO: Outstanding bug in firmware, where CRC32 of GET_SLOTS dataset is not appended. Will get fixed in further FW release */
		if (cmd != GET_SLOTS)
		{
			LOG_ERROR("Dataset CRC32 mismatch!\n");
			// application should decide whether to do re-request
			throw eBadRxCRC();
		}
	}
	LOG_DEBUG("Dataset CRC32 matches\n");

	return total_length;
}

bool Hypstar::sendPacketedData(const char commandId, unsigned char * pDataSet, int datasetLength, const char *pCommandIdString)
{
	unsigned short totalPacketCount = ceil((float)datasetLength/DATA_PACKET_BODY_SIZE_MAX);
	unsigned char *pDatasetHead = pDataSet;

	unsigned char currentPacket[PACKET_BODY_SIZE_MAX];
	unsigned short *pPacketNumber = (unsigned short*)&currentPacket[0];
	*(unsigned short*) &currentPacket[2] = totalPacketCount;
	*pPacketNumber = 0;
	unsigned short packetLength = DATA_PACKET_BODY_SIZE_MAX;
	long datasetEndAddress = (long)pDataSet + (long)datasetLength;
	do
	{
		memcpy(&currentPacket[4], pDatasetHead, packetLength);
		long chunk = (long)pDatasetHead-(long)pDataSet;
		LOG_DEBUG("Sending packet %d/%d (bytes [%lu..%lu]/%lu) \n", *pPacketNumber+1, totalPacketCount, chunk, chunk+packetLength,  datasetLength);
		// @TODO: should unify this in firmware (FW returns DONE, while CAL_COEFS returns ACK on last packet
		// +4 packetLength here to include space for packet number/total number without affecting tracking of location in dataset
		if (((commandId & 0xFF) == FW_DATA) && ((totalPacketCount-1) == *pPacketNumber))
		{
			sendAndWaitForDone(commandId, currentPacket, packetLength+4, pCommandIdString, 5);
		}
		else
		{
			sendAndWaitForAcknowledge(commandId, currentPacket, packetLength+4, pCommandIdString);
		}

		// Increment dataset pointer
		pDatasetHead = pDatasetHead + packetLength;
		// Check and adjust length of next packet
		if (((long)pDatasetHead + DATA_PACKET_BODY_SIZE_MAX) > datasetEndAddress)
		{
			LOG_TRACE("Start: %p, Head: %p, next head: %p, end: %p\n", pDataSet, pDatasetHead, (char*)(pDatasetHead + DATA_PACKET_BODY_SIZE_MAX), (char*)datasetEndAddress);
			packetLength = (long)datasetEndAddress - (long)pDatasetHead;
		}

		LOG_DEBUG("Instrument accepted packet %d/%d\n", ++*pPacketNumber, totalPacketCount);
	} while (*pPacketNumber < totalPacketCount);
	return false;
}

bool Hypstar::getHardWareInfo(void)
{
	exchange(BOOTED, NULL, 0, "BOOTED", 0.1);
	memcpy(&hw_info, (rxbuf + 3), sizeof(struct s_booted));

	LOG_DEBUG("memory slots %hu, vnir=%d, swir=%d, mux=%d, cam=%d, accel=%d, rh=%d, pressure=%d, swir_tec=%d SD=%d, PM1=%d, PM2=%d\n",
			hw_info.memory_slot_count, hw_info.vnir_module_available, hw_info.swir_module_available, hw_info.optical_multiplexer_available, hw_info.camera_available,
			hw_info.accelerometer_available, hw_info.humidity_sensor_available, hw_info.pressure_sensor_available, hw_info.swir_tec_module_available, hw_info.sd_card_available, hw_info.power_monitor_1_available, hw_info.power_monitor_2_available);

	return true;
}

bool Hypstar::getCalibrationCoefficientsBasic(void)
{
	struct s_calibration_coefficients_raw *coefs_raw;
		char tmp[15];
		int rx_count;
		int i;

		// get standard set of calibration coefficients
		rx_count = REQUEST(GET_CAL_COEF);

		if ((rx_count - 4) != (int)sizeof(struct s_calibration_coefficients_raw))
		{
			LOG_ERROR("Received calibration coefficients data packet (%d) does not match the size of packet structure (%zu)\n", (rx_count - 4), sizeof(struct s_calibration_coefficients_unpacked));
			return false;
		}

		coefs_raw = (struct s_calibration_coefficients_raw *)(rxbuf + 3);

		// vnir wl coefs
		for (i = 0; i < 6; i++)
		{
			memcpy(tmp, coefs_raw->vnir_wavelength_coefficientss_raw + i * 14, 14);
			tmp[14] = 0;
			calibration_coefficients_basic.vnir_wavelength_coefficients[i] = atof(tmp);

			LOG_DEBUG("VNIR wl coef %d: \"%s\" = %+.7e\n", i, tmp, calibration_coefficients_basic.vnir_wavelength_coefficients[i]);
		}

		// vnir lin coefs
		for (i = 0; i < 8; i++)
		{
			memcpy(tmp, coefs_raw->vnir_linerity_coefficients_raw + i * 14, 14);
			tmp[14] = 0;
			calibration_coefficients_basic.vnir_linearity_coefficients[i] = atof(tmp);

			LOG_DEBUG("VNIR lin coef %d: \"%s\" = %+.7e\n", i, tmp, calibration_coefficients_basic.vnir_linearity_coefficients[i]);
		}

		// swir wl coefs
		for (i = 0; i < 5; i++)
		{
			memcpy(tmp, coefs_raw->swir_wavelength_coefficients_raw + i * 14, 14);
			tmp[14] = 0;
			calibration_coefficients_basic.swir_wavelength_coefs[i] = atof(tmp);

			// remove CR
			for (int j = 0; j < 14; j++)
				if (tmp[j] == 0x0D)
				{
					tmp[j] = 0;
					break;
				}

			LOG_DEBUG("SWIR wl coef %d: \"%s\" = %+.7e\n", i, tmp, calibration_coefficients_basic.swir_wavelength_coefs[i]);
		}

		// accelerometer cal coefs
		for (i = 0; i < 3; i++)
		{
			calibration_coefficients_basic.accelerometer_horizontal_reference[i] = coefs_raw->accelerometer_horizontal_reference[i];
			LOG_DEBUG("Accelerometer cal coef %d: %hu\n", i, calibration_coefficients_basic.accelerometer_horizontal_reference[i]);
		}
		return true;
}

bool Hypstar::getCalibrationCoefficientsExtended(void)
{
	unsigned char *p_cal_data;

	// get extended set of calibration coefficients
	p_cal_data = (unsigned char*)(&extended_calibration_coefficients);

	try
	{
		GET_PACKETED_DATA(GET_CAL_COEF, NULL, 0, p_cal_data);
	}

	// uninitialised flash is filled with 0xFF, including the CRC32 bytes.
	// in this case, skip the CRC32 check
	catch (eBadRxCRC &e)
	{
//		if (ext_cal_coefs.crc32 == 0xFFFFFFFF)
		{
			LOG_ERROR("Extended calibration coefficients not available (at least CRC32 isn't)\n");
		}
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Caught unhandled eHypstar exception, failed to get calibration coefficients\n");
		return false;
	}

	return true;
}

bool Hypstar::getCalibrationCoefficientsAll(void)
{
	bool retval = false;
	retval = getCalibrationCoefficientsBasic();
	if (!retval) {
		return retval;
	}
	return getCalibrationCoefficientsExtended();
}

uint64_t Hypstar::getTime(void)
{
	uint64_t *tm;
	REQUEST(GET_SYSTIME);
	tm = (uint64_t *)(rxbuf + 3);
	return (*tm);
}


bool Hypstar::setTime(uint64_t time_s)
{
	EXCHANGE(SET_SYSTIME, (unsigned char *)&time_s, (unsigned short)sizeof(time_s));
	return true;
}

bool Hypstar::getEnvironmentLogEntry(struct s_environment_log_entry *pTarget, unsigned char index)
{
	try
	{
		EXCHANGE(GET_ENV, &index, 1);
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Failed to get envlog\n");
		return false;
	}

	memcpy(pTarget, (rxbuf + 3), sizeof(struct s_environment_log_entry));
	return true;
}

bool Hypstar::setBaudRate(e_baudrate baudRate)
{
	try
	{
		SEND_AND_WAIT_FOR_ACK(SET_BAUD, (unsigned char *)&baudRate, (unsigned short)sizeof(baudRate));

		/* switch terminal baudrate and wait for DONE packet from the instrument */
		hnport->setBaud((int)baudRate);
		readData(1.0); // DONE

		if ((rxbuf[0] != DONE) || (rxbuf[3] != SET_BAUD))
		{
			LOG_ERROR("Did not receive DONE after switching baud rate\n");
			return false;
		}
		LOG_DEBUG("Successfully switched baudrate to %d\n", baudRate);
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Failed to switch baud rate\n");
		return false;
	}

	return true;
}

int Hypstar::acquireJpegImage(bool flip, bool mirror, bool autoFocus, struct s_img_data_holder *pImageDatasetTarget)
{
	s_capture_image_request_flags flags = {
			.scale = 0,
			.flip_v = flip,
			.mirror_h = mirror,
			.auto_focus = autoFocus
	};
	int img_size = captureJpegImage(JPG_5MP, flags, 30.0);
	if (!img_size) {
		return 0;
	}
	getImage(pImageDatasetTarget);

	return pImageDatasetTarget->image_size;
}

unsigned short Hypstar::captureImage(struct s_capture_image_request captureRequestParameters, float timeout_s)
{
	// clear not used flags
	captureRequestParameters.flags.na = 0;

	try
	{
		if (!SEND_AND_WAIT_FOR_ACK_AND_DONE(CAPTURE_MM_IMG, (unsigned char*)&captureRequestParameters, (unsigned short)sizeof(struct s_capture_image_request), timeout_s))
		{
			LOG_ERROR("Failed to capture image\n");
			return 0;
		}
		return *((unsigned short*)(rxbuf + 4));
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Failed to capture image\n");
	}

	return 0;
}


unsigned short Hypstar::captureJpegImage(enum e_jpg_resolution resolution, struct s_capture_image_request_flags flags, float timeout_s)
{
	struct s_capture_image_request cap_img;

	switch(resolution)
	{
	case QQVGA:
		cap_img.resolution_h = 160;
		cap_img.resolution_v = 120;
		break;
	case QCIF:
		cap_img.resolution_h = 176;
		cap_img.resolution_v = 144;
		break;
	case QVGA:
		cap_img.resolution_h = 320;
		cap_img.resolution_v = 240;
		break;
	case WQVGA:
		cap_img.resolution_h = 400;
		cap_img.resolution_v = 240;
		break;
	case CIF:
		cap_img.resolution_h = 352;
		cap_img.resolution_v = 288;
		break;
	case VGA:
		cap_img.resolution_h = 640;
		cap_img.resolution_v = 480;
		break;
	case WVGA:
		cap_img.resolution_h = 800;
		cap_img.resolution_v = 600;
		break;
	case XGA:
		cap_img.resolution_h = 1024;
		cap_img.resolution_v = 768;
		break;
	case JPG_720p:
		cap_img.resolution_h = 1280;
		cap_img.resolution_v = 720;
		break;
	case SXGA:
		cap_img.resolution_h = 2080;
		cap_img.resolution_v = 960;
		break;
	case UXGA:
		cap_img.resolution_h = 1600;
		cap_img.resolution_v = 1200;
		break;
	case JPG_1080p:
		cap_img.resolution_h = 1920;
		cap_img.resolution_v = 1080;
		break;
	case WUXGA:
		cap_img.resolution_h = 1920;
		cap_img.resolution_v = 1200;
		break;
	case QXGA:
		cap_img.resolution_h = 2048;
		cap_img.resolution_v = 1536;
		break;
	case JPG_5MP:
	default:
		cap_img.resolution_h = 2592;
		cap_img.resolution_v = 1944;
		break;
	}

	cap_img.flags = flags;
	cap_img.flags.na = 0;
	cap_img.flags.auto_focus = false;
	cap_img.format = JPEG;

	return captureImage(cap_img, timeout_s);
}


int Hypstar::getImage(struct s_img_data_holder *pImageDatasetTarget)
{
	int total_length = 0;

	try
	{
		memset(pImageDatasetTarget, 0, sizeof(struct s_img_data_holder));

		total_length = GET_PACKETED_DATA(GET_MM_IMG, NULL, 0, (unsigned char*)pImageDatasetTarget);
		pImageDatasetTarget->image_size = total_length;
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Failed to get image\n");
	}

	return total_length;
}

unsigned short Hypstar::captureSpectra(enum e_radiometer spectrumType, enum e_entrance entranceType, unsigned short vnirIntegrationTime_ms,
		unsigned short swirIntegrationTime_ms, unsigned short scanCount, unsigned short seriesMaxDuration_s)
{
	struct s_capture_spectra_request_packet capture_spec_packet;
	unsigned short n_captures = 0;
	float timeout_s = READTIMEOUT;

	// zero-initialize all parameter flags
	capture_spec_packet.capture_spectra_parameters = s_spectrum_optical_configuration();

	if (spectrumType == VNIR || spectrumType == BOTH)
		capture_spec_packet.capture_spectra_parameters.vnir = 1;

	if (spectrumType == SWIR || spectrumType == BOTH)
		capture_spec_packet.capture_spectra_parameters.swir = 1;

	if (entranceType == RADIANCE)
		capture_spec_packet.capture_spectra_parameters.radiance = 1;

	if (entranceType == IRRADIANCE)
		capture_spec_packet.capture_spectra_parameters.irradiance = 1;

	capture_spec_packet.vnir_integration_time_ms = vnirIntegrationTime_ms;
	capture_spec_packet.swir_integration_time_ms = swirIntegrationTime_ms;
	capture_spec_packet.scan_count = scanCount;
	capture_spec_packet.maximum_total_series_time_s = seriesMaxDuration_s;

	LOG_DEBUG("vnir=%d, swir=%d, L=%d, E=%d, v_it=%hu, s_it=%hu, scan_count=%hu, series_time=%hu\n",
			capture_spec_packet.capture_spectra_parameters.vnir, capture_spec_packet.capture_spectra_parameters.swir,
			capture_spec_packet.capture_spectra_parameters.radiance, capture_spec_packet.capture_spectra_parameters.irradiance,
			capture_spec_packet.vnir_integration_time_ms, capture_spec_packet.swir_integration_time_ms,
			capture_spec_packet.scan_count, capture_spec_packet.maximum_total_series_time_s);

	if (!SEND_AND_WAIT_FOR_ACK(CAPTURE_SPEC, (unsigned char *)&capture_spec_packet, (unsigned short)sizeof(struct s_capture_spectra_request_packet)))
	{
		LOG_ERROR("Failed to capture spectra\n");
		return 0;
	}

	try
	{
		// fixed integration time
		if (((capture_spec_packet.capture_spectra_parameters.vnir == 0) || (vnirIntegrationTime_ms != 0)) &&
				((capture_spec_packet.capture_spectra_parameters.swir == 0) || (swirIntegrationTime_ms != 0)))
		{
			LOG_DEBUG("Capture fixed IT\n");
			unsigned short max_inttime = (vnirIntegrationTime_ms > swirIntegrationTime_ms ? vnirIntegrationTime_ms : swirIntegrationTime_ms);
			lastCaptureLongestIntegrationTime_ms = max_inttime;

			if ((scanCount != 0) && (seriesMaxDuration_s == 0))
				// expected scan_count * inttime * 1.2 + 0.2 seconds
				timeout_s = CAPTURE_TIMEOUT_MULT * scanCount * (max_inttime / 1000.0 + CAPTURE_TIMEOUT_ADD_EACH) + CAPTURE_TIMEOUT_ADD;
			else if ((scanCount == 0) && (seriesMaxDuration_s != 0))
				// expected series_time * 1.2 + 0.2 seconds
				timeout_s = CAPTURE_TIMEOUT_MULT * seriesMaxDuration_s + CAPTURE_TIMEOUT_ADD;
			else if ((scanCount != 0) && (seriesMaxDuration_s != 0))
			{
				timeout_s = (((max_inttime / 1000.0 + CAPTURE_TIMEOUT_ADD_EACH) * scanCount) > seriesMaxDuration_s ?
								((max_inttime / 1000.0 + CAPTURE_TIMEOUT_ADD_EACH) * scanCount) : seriesMaxDuration_s);
				timeout_s = timeout_s * CAPTURE_TIMEOUT_MULT + CAPTURE_TIMEOUT_ADD;
			}
			else
			{
				// should receive error if both are 0
				timeout_s = CAPTURE_TIMEOUT_ADD;
			}

			LOG_DEBUG("Waiting for done fixed IT\n");
			if (!WAIT_FOR_DONE(CAPTURE_SPEC, timeout_s))
			{
				return 0;
			}
		}
		else // Automatic integration time: vnir_inttime_ms == 0 || swir_inttime_ms == 0
		{
			// DARK auto integration time should reuse last used exposure, otherwise it would adjust itself to infinity and beyond
			if (entranceType == DARK)
			{
				timeout_s = scanCount * lastCaptureLongestIntegrationTime_ms * 1e-3 * CAPTURE_TIMEOUT_MULT + CAPTURE_TIMEOUT_ADD;
				/* If driver has been (re)instantiated between calls, but instrument has been working,
				 * We don't know what is the last capture integration time, so we default to maximum.
				 */
				if (!lastCaptureLongestIntegrationTime_ms)
				{
					timeout_s = 66;
				}
				WAIT_FOR_DONE(CAPTURE_SPEC, timeout_s);
			}
			else
			{
				lastCaptureLongestIntegrationTime_ms = 0;
				struct s_automatic_integration_time_adjustment_status status;
				int k = 1;
				float next_timeout;

				timeout_s = 1.0;

				while(true)
				{
					readData(timeout_s);

					if ((rxbuf[0] == DONE) && (rxbuf[3] == CAPTURE_SPEC))
						break;

					if (rxbuf[0] == AUTOINT_STATUS)
					{

						memcpy(&status, (rxbuf + 3), sizeof(struct s_automatic_integration_time_adjustment_status));
						next_timeout = status.next_integration_time_ms * 1e-3 * CAPTURE_TIMEOUT_MULT * scanCount + CAPTURE_TIMEOUT_ADD;

						// if vnir and swir packets are mixed and integration times
						// are different it is possible that the module with shorter
						// integration time reports next_inttime_ms that is too short
						// for the other module
						if (next_timeout > timeout_s)
						{
							timeout_s = next_timeout;
						}

						std::stringstream dbg_out;
						dbg_out << "Autoadjust inttime step " << k++ << ": spec=";

						if (status.spectrum_config.vnir && status.spectrum_config.swir)
							dbg_out << "both";
						else if (status.spectrum_config.vnir)
							dbg_out << "VNIR";
						else if (status.spectrum_config.swir)
							dbg_out << "SWIR";
						else
							dbg_out << "none";

						dbg_out << ", entrance=";
						if (status.spectrum_config.radiance)
							dbg_out << "L";
						else if (status.spectrum_config.irradiance)
							dbg_out << "E";
						else
							dbg_out << "dark";

						dbg_out << ", this_inttime_ms=" << status.current_integration_time_ms << ", peak_adc=" << status.peak_adc_value << ", next_inttime_ms=" << status.next_integration_time_ms << "\n",

						dbg_out << "vnir=" << status.spectrum_config.vnir << ", swir=" << status.spectrum_config.swir \
							<< ", radiance=" << status.spectrum_config.radiance << ", irradiance=" \
							<< status.spectrum_config.irradiance << " , slot=" << status.memory_slot_id;
						LOG_DEBUG("%s\n", dbg_out.str().c_str());

						// save last capture integration time, to provide correct read timeout, since DARK automatic integration time uses that
						lastCaptureLongestIntegrationTime_ms = status.next_integration_time_ms > lastCaptureLongestIntegrationTime_ms ? status.next_integration_time_ms : lastCaptureLongestIntegrationTime_ms;
					}
				}
			}
		} // inttime_ms == 0, automatic integration time is set now

		// rxbuf[0] == DONE
		n_captures = *((unsigned short*)(rxbuf + 4));

		LOG_DEBUG("Captured %d spectra\n", n_captures);
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Failed to capture spectrum\n");
		return 0;
	}

	return n_captures;
}

unsigned short Hypstar::getLastSpectraCaptureMemorySlots(unsigned short *pMemorySlotIdTarget, unsigned short numberOfCaptures)
{
	unsigned short slot_count = 0;
	int i;
	slot_count = (GET_PACKETED_DATA(GET_SLOTS, NULL, 0, (unsigned char*)pMemorySlotIdTarget) / sizeof(unsigned short));

	if (slot_count != numberOfCaptures)
	{
		LOG_ERROR("Memory slot count (%d) does not match number of captured spectra (%d).\n", slot_count, numberOfCaptures);
		return 0;
	}

	std::stringstream dbg_out;
	dbg_out << "Captured " << numberOfCaptures << " spectra in slots";

	for (i = 0; i < numberOfCaptures; i++)
	{
		dbg_out << " " << pMemorySlotIdTarget[i];
	}

	LOG_DEBUG("%s\n", dbg_out.str().c_str());
	return slot_count;
}

unsigned short Hypstar::getSpectraFromMemorySlots(unsigned short *pMemorySlotIds, unsigned short numberOfCaptures, struct s_spectrum_dataset *pSpectraDataTarget)
{
	unsigned char *p_spec_data;
	unsigned short n = 0, n_success = 0;
	unsigned short spectrum_length = 0;

	try
	{
		for (n = 0; n < numberOfCaptures; n++)
		{
			p_spec_data = (unsigned char*)(pSpectraDataTarget + n_success);

			// clear for CRC calculation
			memset(pSpectraDataTarget[n_success].spectrum_body, 0, MAX_SPEC_LENGTH * sizeof(unsigned short));
			LOG_DEBUG("Getting spec %d from slot %d\n", n, pMemorySlotIds[n]);

			spectrum_length = GET_PACKETED_DATA(GET_SPEC, (unsigned char*)&pMemorySlotIds[n], sizeof(pMemorySlotIds[n]), p_spec_data);
			LOG_DEBUG("Spectrum total_length=%d, crc_slot pointer = %p, target slot pointer = %p, crc32_in position = 0x%.8X\n",
					spectrum_length, p_spec_data, (void*)((long)p_spec_data+spectrum_length-4),
					*((uint32_t*) ((long)p_spec_data+spectrum_length-4) ));

			// copy over CRC32 to the correct position for SWIR dataset and remove CRC32 from spectral data body
			if (pSpectraDataTarget[n].spectrum_header.spectrum_config.swir)
			{
				memcpy(&pSpectraDataTarget[n].crc32_spaceholder, (uint32_t*) ((long)p_spec_data+spectrum_length-4), sizeof(typeof(pSpectraDataTarget[n_success].crc32_spaceholder)));
				memset(&pSpectraDataTarget[n].spectrum_body[256], 0, 4);
			}

			n_success++;
		}
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Caught unhandled eHypstar exception, failed to get spectrum\n");
	}

	return n_success;
}


unsigned short Hypstar::getSingleSpectrumFromMemorySlot(unsigned short memorySlotId, struct s_spectrum_dataset * pSpectraDataTarget)
{
	return getSpectraFromMemorySlots(&memorySlotId, 1, pSpectraDataTarget);
}

unsigned short Hypstar::acquireSpectra(enum e_radiometer spectrumType, enum e_entrance entranceType, unsigned short vnirIntegrationTime_ms,
		unsigned short swirIntegrationTime_ms, unsigned short scanCount, unsigned short seriesMaxDuration_s, s_spectrum_dataset *pSpectraTarget)
{
	unsigned short cnt = captureSpectra(spectrumType, entranceType, vnirIntegrationTime_ms, swirIntegrationTime_ms, scanCount, seriesMaxDuration_s);
	unsigned short slots[cnt];
	getLastSpectraCaptureMemorySlots(slots, cnt);
	getSpectraFromMemorySlots(slots, cnt, pSpectraTarget);
	return cnt;
}

std::vector<Spectrum> Hypstar::acquireSpectraVector(enum e_radiometer spectrumType, enum e_entrance entranceType, unsigned short vnirIntegrationTime_ms,
		unsigned short swirIntegrationTime_ms,	unsigned short scanCount, unsigned short seriesMaxDuration_s)
{
	unsigned short cnt = captureSpectra(spectrumType, entranceType, vnirIntegrationTime_ms, swirIntegrationTime_ms, scanCount, seriesMaxDuration_s);
	unsigned short slots[cnt];
	getLastSpectraCaptureMemorySlots(slots, cnt);
	s_spectrum_dataset specs[cnt];
	getSpectraFromMemorySlots(slots, cnt, specs);

	std::vector<Spectrum> ret_val;
	for (int i = 0; i < cnt; i++) {
		ret_val.push_back(Spectrum(&specs[i]));
	}
	return ret_val;
}

bool Hypstar::setTECSetpoint(float setpoint_C)
{
	if ((setpoint_C != TEC_OFF) && ((setpoint_C < MIN_TEC_SETPOINT) || (setpoint_C > MAX_TEC_SETPOINT)))
	{
		LOG_ERROR("TEC setpoint (%.1f) is outside the allowed range [%.1f ... %.1f]\n\n",
				setpoint_C, MIN_TEC_SETPOINT, MAX_TEC_SETPOINT);

		return false;
	}

	try
	{
		return SEND_AND_WAIT_FOR_ACK_AND_DONE(SET_SWIR_TEMP, (unsigned char *)&setpoint_C, (unsigned short)sizeof(setpoint_C), 120);
	}
	catch (eHypstar &e)
	{
		LOG_ERROR("Failed to stabilize SWIR temperature\n");
		return false;
	}

	return true;
}

bool Hypstar::shutdown_TEC(void)
{
	return setTECSetpoint(-100);
}

bool Hypstar::enterFlashWriteMode(void)
{
	// dummy length, another protection method
	int fw_len = 100000;
	return SEND_AND_WAIT_FOR_DONE(ENTER_FLASH_WRITE_MODE, (unsigned char *)&fw_len, (unsigned short)sizeof(fw_len));
}

bool Hypstar::sendCalibrationCoefficients(s_extended_calibration_coefficients *pNewExternalCalibrationCoeficients)
{
	LOG_DEBUG("Starting calibration coefficient upload, ptr: %p\n", pNewExternalCalibrationCoeficients);
	LOG_DEBUG("Cal date in send coefs: %d-%d-%d\n", pNewExternalCalibrationCoeficients->calibration_year, pNewExternalCalibrationCoeficients->calibration_month, pNewExternalCalibrationCoeficients->calibration_day);
	// update dataset crc32
	pNewExternalCalibrationCoeficients->crc32 = 0;

	int total_length = sizeof(s_extended_calibration_coefficients);
	int crc32_buflen = ((total_length - 4) % 4) ?
			(total_length - 4) + 4 - ((total_length - 4) % 4) :
			(total_length - 4);

	int calc_crc32 = Compute_CRC32_BE(crc32_buflen, (unsigned char*)pNewExternalCalibrationCoeficients);
	pNewExternalCalibrationCoeficients->crc32 = calc_crc32;
	LOG_DEBUG("Calibration coefficient crc32: 0x%08X\n", pNewExternalCalibrationCoeficients->crc32);

	// According to "protection from user" logic, we should already be in FLASH_WRITE mode
	return SEND_PACKETED_DATA(SET_CAL_COEF, (unsigned char *) pNewExternalCalibrationCoeficients, sizeof(s_extended_calibration_coefficients));
}

bool Hypstar::saveCalibrationCoefficients(void)
{
	return SEND_AND_WAIT_FOR_ACK_AND_DONE(SAVE_CAL_COEF, 0, 0, 5);
}

bool Hypstar::getFirmwareInfo(void)
{
	if ((firmware_info.firmware_version_minor == 0) && (firmware_info.firmware_version_major == 0))
	{
		bool r = REQUEST(GET_FW_VER);
		if (r)
		{
			memcpy(&firmware_info, (rxbuf + 3), sizeof(struct s_firwmare_info));
			return true;
		}
		else
		{
			return false;
		}
	}
	return true;
}

bool Hypstar::sendNewFirmwareData(std::string filePath) {
	std::ifstream binFile(filePath.c_str(), std::ios::in | std::ios::binary);
	if (!binFile) {
		return false;
	}

	std::vector<unsigned char> buffer(std::istreambuf_iterator<char>(binFile), {});

	binFile.close();

	int crc32_buflen = ((buffer.size() - 4) % 4) ?
			(buffer.size()) + 4 - ((buffer.size() ) % 4) :
			(buffer.size());

	uint32_t calc_crc32 = Compute_CRC32_BE(crc32_buflen, (unsigned char*)buffer.data());
	std::vector<unsigned char> crcvec(((unsigned char*)&calc_crc32), ((unsigned char*)&calc_crc32)+4);
	buffer.insert(buffer.end(), crcvec.begin(), crcvec.end());
	LOG_DEBUG("Firmware buffer length with CRC: %lu, CRC: %08X, in buf: %08X\n", buffer.size(), calc_crc32, *(uint32_t*)&buffer[buffer.size()-4]);

	unsigned int size = buffer.size();
	// notify the instrument about length of our new firmware
	SEND_AND_WAIT_FOR_DONE(ENTER_FLASH_WRITE_MODE, (unsigned char *)&size, 4);
	return SEND_PACKETED_DATA(FW_DATA, (unsigned char *) buffer.data(), size);
}

bool Hypstar::saveNewFirmwareData(void) {
	return exchange(SAVE_NEW_FW, 0, 0, "SAVE_NEW_FW", 30);
}

bool Hypstar::switchFirmwareSlot(void) {
	memset(&firmware_info, 0, sizeof(s_firwmare_info));
	return exchange(BOOT_NEW_FW, 0, 0, "BOOT_NEW_FW", 30);
}

/* C wrapper functions */
struct hs_object_holder
{
	void *hs_instance;
};

static std::vector<hypstar_t*> object_holder_instances;

hypstar_t* hypstar_init(const char *port)
{
	hypstar_t *hs_wrapper;
	Hypstar *obj;
	obj = Hypstar::getInstance(port);

	/* Try getting instance. Duplicate port checks are done within class itself
	 * If returned instance is already in some wrapper, return that wrapper
	*/
	for (hypstar_t *i : object_holder_instances)
	{
		if (i->hs_instance == obj)
		{
			return i;
		}
	}
	// otherwise instantiate new wrapper and append to object_holder_instances
	hs_wrapper = (typeof(hs_wrapper)) malloc(sizeof(*hs_wrapper));
	hs_wrapper->hs_instance = obj;
	object_holder_instances.push_back(hs_wrapper);
	return hs_wrapper;
}

void hypstar_close(hypstar_t *hs)
{
	if (hs == NULL)
	{
		return;
	}

	// find and delete existing wrapper from vector
	for (uint i = 0; i < object_holder_instances.size(); i++)
	{
		if (object_holder_instances[i]->hs_instance == hs->hs_instance)
		{
			object_holder_instances.erase(object_holder_instances.begin()+i);
			delete static_cast<Hypstar *> (hs->hs_instance);
			free(hs);
		}
	}
}

void hypstar_set_loglevel(hypstar_t *hs, e_loglevel loglevel)
{
	if (hs == NULL)
	{
		return;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	instance->setLoglevel(loglevel);
}

uint64_t hypstar_get_time(hypstar_t *hs)
{
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->getTime();
}

bool hypstar_set_time(hypstar_t *hs, uint64_t time)
{
	if (hs == NULL)
	{
		return false;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	instance->setTime(time);
	return true;
}

bool hypstar_get_hw_info(hypstar_t *hs, s_booted *target)
{
	if (hs == NULL)
	{
		return false;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	bool response = instance->getHardWareInfo();
	if (!response)
	{
		return response;
	}
	memcpy(target, &instance->hw_info, sizeof(instance->hw_info));
	return response;
}

bool hypstar_get_env_log(hypstar_t *hs, unsigned char index, s_environment_log_entry *target)
{
	if (hs == NULL)
	{
		return false;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	bool response = instance->getEnvironmentLogEntry(target, index);

	return response;
}

bool hypstar_get_calibration_coefficients_basic(hypstar_t *hs, s_calibration_coefficients_unpacked *coef_target)
{
	if (hs == NULL)
	{
		return false;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	bool response = instance->getCalibrationCoefficientsBasic();
	if (!response)
	{
		return response;
	}
	memcpy(coef_target, &instance->calibration_coefficients_basic, sizeof(s_calibration_coefficients_unpacked));

	return response;
}

bool hypstar_get_calibration_coefficients_extended(hypstar_t *hs, s_extended_calibration_coefficients *ext_cal_coef_target)
{
	if (hs == NULL)
	{
		return false;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	bool response = instance->getCalibrationCoefficientsExtended();
	if (!response)
	{
		return response;
	}
	memcpy(ext_cal_coef_target, &instance->extended_calibration_coefficients, sizeof(s_extended_calibration_coefficients));

	return response;
}

bool hypstar_get_calibration_coefficients_all(hypstar_t *hs, s_calibration_coefficients_unpacked *coef_target, s_extended_calibration_coefficients *ext_cal_coef_target)
{
	if (hs == NULL)
	{
		return false;
	}
	bool response = hypstar_get_calibration_coefficients_basic(hs, coef_target);
	if (!response)
	{
		return response;
	}
	return hypstar_get_calibration_coefficients_extended(hs, ext_cal_coef_target);
}

unsigned short hypstar_capture_spectra(hypstar_t *hs, enum e_radiometer spec, enum e_entrance mux,
		unsigned short vnir_inttime_ms, unsigned short swir_inttime_ms, unsigned short scan_count, unsigned short series_time_s)
{
	if (hs == NULL)
	{
		return false;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->captureSpectra(spec, mux, vnir_inttime_ms, swir_inttime_ms, scan_count, series_time_s);
}

unsigned short hypstar_get_last_capture_memory_slots(hypstar_t *hs, unsigned short *target, unsigned short number_of_captures)
{
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->getLastSpectraCaptureMemorySlots(target, number_of_captures);
}

unsigned short hypstar_download_spectra(hypstar_t *hs, unsigned short *memory_slots, unsigned short number_of_captures, s_spectrum_dataset *target)
{
	if (hs == NULL)
	{
		return 0;
	}

	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->getSpectraFromMemorySlots(memory_slots, number_of_captures, target);
}

unsigned short hypstar_acquire_spectra(hypstar_t *hs, enum e_radiometer spec, enum e_entrance mux,
		unsigned short vnir_inttime_ms,	unsigned short swir_inttime_ms,	unsigned short scan_count, unsigned short series_time_s, s_spectrum_dataset *target)
{
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->acquireSpectra(spec, mux, vnir_inttime_ms, swir_inttime_ms, scan_count, series_time_s, target);
}

bool hypstar_set_baudrate(hypstar_t *hs, e_baudrate new_baudrate)
{
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->setBaudRate(new_baudrate);
}

unsigned short hypstar_capture_JPEG_image(hypstar_t *hs, bool flip, bool mirror, bool auto_focus)
{
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	s_capture_image_request_flags flags = {
			.scale = 0,
			.flip_v = flip,
			.mirror_h = mirror,
			.auto_focus = auto_focus,
			.na = 0
	};
	return instance->captureJpegImage(JPG_5MP, flags, 10.0);
}

unsigned short hypstar_download_JPEG_image(hypstar_t *hs, s_img_data_holder *target)
{
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->getImage(target);
}

bool hypstar_set_TEC_target_temperature(hypstar_t *hs, float target_temp_deg_C) {
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->setTECSetpoint(target_temp_deg_C);
}

bool hypstar_shutdown_TEC(hypstar_t *hs) {
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->shutdown_TEC();
}

bool hypstar_reboot(hypstar_t *hs) {
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->reboot();
}

bool hypstar_enter_flash_write_mode(hypstar_t *hs) {
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->enterFlashWriteMode();
}

bool hypstar_send_calibration_coefficients(hypstar_t *hs, s_extended_calibration_coefficients *pNewExternalCalibrationCoeficients) {
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->sendCalibrationCoefficients(pNewExternalCalibrationCoeficients);
}

bool hypstar_save_calibration_coefficients(hypstar_t *hs) {
	if (hs == NULL)
	{
		return 0;
	}
	Hypstar *instance = static_cast<Hypstar *>(hs->hs_instance);
	return instance->saveCalibrationCoefficients();
}

// @TODO: acceleration to Gs and gravity vector offset
// @TODO: automatic IT callbacks on adjust
// @TODO: automatic IT callback on done

bool hypstar_test_callback(hypstar_t *hs, void(*cb_function)(s_automatic_integration_time_adjustment_status*), int paramA, int paramB)
{
	s_spectrum_optical_configuration spectrum_config = {
			.na = 0,
			.irradiance = 0,
			.radiance = 1,
			.semolator_fake_saturation = 0,
			.swir = 0,
			.vnir = 1,
	};
	s_automatic_integration_time_adjustment_status s = {
			.spectrum_config = spectrum_config,
			.current_integration_time_ms = 64,
			.peak_adc_value = 12345,
			.next_integration_time_ms = 128,
			.memory_slot_id = 15
	};
	(*cb_function)(&s);
	return true;
}
