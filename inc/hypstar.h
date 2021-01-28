/**
 * \brief	Hypstar instrument Linux driver with Python support via Boost.Python
 *	Tested on 64bit Debian-based system with Python 3.8
 *
 *	\usage	1. Instantiate Hypstar *hs = Hypstar::getInstance(port);
 *			2. Switch baudrate hs->setBaudRate(B_6000000)
 *			3. Call functions
 *			4. Destroy if needed.
 *
 *	\author Joel Kuusk, Kaspars Laizans (Tartu Observatory)
 */

#ifndef LIBHYPSTAR_H
#define LIBHYPSTAR_H

#include <stdio.h>
#include "linuxserial.h"
#include <string>
#include "hypstar_typedefs.hpp"
#include <vector>
#include <stdarg.h>
#include <iostream>

using namespace LibHypstar;

/**
 * Main driver class. Handles communications with the instrument
 * with input parameter sanity checks and some level of error recovery.
 *
 */
class Hypstar
{
	struct s_hypstar_instance {
		std::string port;
		Hypstar *instance;
	};

	public:
		/**
		 * \brief	To avoid multiple access, Singleton-style instantiation is done
		 * New instances are initialized to default baud rate and are reset to it in destructor
		 * On initialization driver sets instrument timestamp to UTC time. Use setTime() to set to local time or whatever
		 * \param portname name of the port (e.g. '/dev/ttyUSB0')
		 */
		static Hypstar* getInstance(std::string portname)
		{
			// look through instance_holder for instance with the same portname
			for (s_hypstar_instance i : Hypstar::instance_holder)
			{
				// if found, return pointer to that
				if (portname.compare(i.port) == 0)
				{
					i.instance->outputLog(INFO, "INFO", stdout, "Returning existing driver instance %p\n", i.instance);
					return i.instance;
				}
			}
			// otherwise instantiate and append to instance_holder
			Hypstar* h = new Hypstar(portname);
			h->outputLog(INFO, "INFO", stdout, "Created driver instance %p\n", static_cast<void*>(h));
			s_hypstar_instance new_hs = {
					.port = portname,
					.instance = h
			};
			Hypstar::instance_holder.push_back(new_hs);
			return h;
			// destructor has to find and remove own entry from the vector
		}

		/**
		 * Destructor. Also resets baud rate to default 115k
		 */
		~Hypstar();

		/* To prevent accidental copying */
		Hypstar(Hypstar const&) = delete;
		void operator = (Hypstar const&) = delete;

		/**
		* \brief	Fills hw_info struct with values. Called on boot.
		 * \return status of execution: True if successful, false if not.
		 */
		bool getHardWareInfo(void);

		/**
		 * \brief	Sets baud rate on the instrument and the used serial port.
		 * \param baud - valid baud rate, can be one of @e_baud
		 * \return status of execution: True if successful, false if not.
		 */
		bool setBaudRate(e_baudrate baudRate);

		/**
		 * \brief	Fills cal_coefs struct with values.
		 * \return status of execution: True if successful, false if not.
		 */
		bool getCalibrationCoefficientsBasic(void);

		/**
		 * \brief	Fills cal_coefs_ext struct with values.
		 * \return status of execution: True if successful, false if not.
		 */
		bool getCalibrationCoefficientsExtended(void);

		/**
		 * \brief	Shorthand for successive requests for basic and extended coefficients
		 * \return status of execution: True if successful, false if not.
		 */
		bool getCalibrationCoefficientsAll(void);

		/**
		 * \brief	 Get instrument internal time
		 * \return UNIX timestamp in milliseconds.
		 */
		uint64_t getTime(void);

		/**
		 * \brief	 Set instrument internal time
		 * \param tm UNIX timestamp in seconds
		 * \return status of execution: True if successful, false if not.
		 */
		bool setTime(uint64_t time_s);

		/**
		 * \brief	 Fill the environment log structure with log data
		 * \param envlog pointer to memory region allocated for log
		 * \param index 0-indexed reverse-order (latest=0) log index to return
		 * \return status of execution: True if successful, false if not.
		 */
		bool getEnvironmentLogEntry(struct s_environment_log_entry *pTarget, unsigned char index);

		/**
		 * \brief	 Capture camera image and store it on the instrument for further retrieval.
		 * \param cap_img image capture parameters
		 * \param timeout_s timeout in seconds for how long to wait for image capture done response
		 * \return size of captured image as a number of data packets to be transferred from the instrument
		 */
		unsigned short captureImage(struct s_capture_image_request captureRequestParameters, float timeout_s);

		/**
		 * \brief	 Shorthand version for image capture, specifically JPEG-compressed
		 * \param res JPEG image resolution, must be one of the standard @e_jpg_resolution
		 * \param flags image capture flags
		 * \param timeout timeout in seconds for how long to wait for image capture done response
		 * \return size of the image in packets
		 */
		unsigned short captureJpegImage(enum e_jpg_resolution resolution, struct s_capture_image_request_flags flags, float timeout_s);

		/**
		 * \brief	 Download image from the instrument
		 * \param img_dataset pointer to allocated image memory location
		 * \return size of the image dataset (including type information, headers and crc32) in bytes
		 */
		int getImage(struct s_img_data_holder *pImageDatasetTarget);

		/**
		 * \brief	 Shorthand for capture and download of a single JPEG image with 5MP resolution
		 * \param flip bool image vertical flip if true
		 * \param mirror bool image horizontal mirror if true
		 * \param autoFocus bool try to auto-focus the camera. If not, focuses to infinity
		 * \param img_dataset pointer to allocated image memory location
		 * \return size of the image dataset (including type information, headers and crc32) in bytes
		 */
		int acquireJpegImage(bool flip, bool mirror, bool autoFocus, struct s_img_data_holder *pImageDatasetTarget);

		/**
		 * \brief	 Capture spectra series (multiple spectra) to the instrument internal memory for subsequent retrieval.
		 * \param spec which radiometer to use: VNIR, SWIR or BOTH
		 * \param mux which optical channel to use: radiance, irradiance or dark
		 * \param vnir_inttime_ms VNIR exposure time. 0 for autoexposure, value in range [1..65635] for fixed exposure time in ms.
		 * \param swir_inttime_ms SWIR exposure time. 0 for autoexposure, value in range [1..65635] for fixed exposure time in ms.
		 * \param scan_count number of exposures to perform
		 * \param series_time_s maximum series duration in seconds, instrument will not exceed this parameter when capturing
		 * \return number of captured spectra
		 */
		unsigned short captureSpectra(enum e_radiometer spectrumType, enum e_entrance entranceType, unsigned short vnirIntegrationTime_ms,
				unsigned short swirIntegrationTime_ms, unsigned short scanCount, unsigned short seriesMaxDuration_s);

		/**
		 * \brief	 Get instrument internal memory slots of last capture series for data acquisition
		 * \param slots pointer to preallocated array to be filled with memory slot addresses
		 * \param n_captures number of captures to obtain, should be equal to return value of captureSpec call
		 * \return number of slots assigned in array, should be equal to n_captures
		 */
		unsigned short getLastSpectraCaptureMemorySlots(unsigned short *pMemorySlotIdTarget, unsigned short numberOfCaptures);

		/**
		 * \brief 	Download spectra data from the instrument.
		 * \param slots pointer to list of memory slots to download from
		 * \param n_captures number of spectra to download
		 * \param spec_data pointer to allocated memory for spectra
		 * \return number of spectra downloaded
		 */
		unsigned short getSpectraFromMemorySlots(unsigned short *pMemorySlotIds, unsigned short numberOfCaptures, struct s_spectrum_dataset *pSpectraDataTarget);

		/**
		 * \brief	Download single spectrum data from the instrument.
		 * \param slot memory slot identifier to download
		 * \param spec_data pointer to preallocated memory to fill
		 * \return number of spectra downloaded
		 */
		unsigned short getSingleSpectrumFromMemorySlot(unsigned short memorySlotId, struct s_spectrum_dataset *pSpectraDataTarget);

		/**
		 * \brief 	Shorthand for "capture spectra" -> "get memory slots" -> "download spectra".
		 *  		Performs all the necessary actions without the need for manual intervention
		 * \param spec which radiometer to use: VNIR, SWIR or BOTH
		 * \param mux which optical channel to use: radiance, irradiance or dark
		 * \param vnir_inttime_ms VNIR exposure time. 0 for autoexposure, value in range [1..65635] for fixed exposure time in ms.
		 * \param swir_inttime_ms SWIR exposure time. 0 for autoexposure, value in range [1..65635] for fixed exposure time in ms.
		 * \param scan_count number of exposures to perform
		 * \param series_time_s maximum series duration in seconds, instrument will not exceed this parameter when capturing
		 * \return vector of Spectrum elements with capture results
		 */
		std::vector<Spectrum> acquireSpectraVector(enum e_radiometer spectrumType, enum e_entrance entranceType, unsigned short vnirIntegrationTime_ms,
				unsigned short swirIntegrationTime_ms, unsigned short scanCount, unsigned short seriesMaxDuration_s);

		/**
		 * \brief 	Shorthand for "capture spectra" -> "get memory slots" -> "download spectra".
		 *  		Performs all the necessary actions without the need for manual intervention
		 * \param spec which radiometer to use: VNIR, SWIR or BOTH
		 * \param mux which optical channel to use: radiance, irradiance or dark
		 * \param vnir_inttime_ms VNIR exposure time. 0 for autoexposure, value in range [1..65635] for fixed exposure time in ms.
		 * \param swir_inttime_ms SWIR exposure time. 0 for autoexposure, value in range [1..65635] for fixed exposure time in ms.
		 * \param scan_count number of exposures to perform
		 * \param series_time_s maximum series duration in seconds, instrument will not exceed this parameter when capturing
		 * \param target Target memory location pointer, must be preallocated
		 * \return number of captures performed
		 */
		unsigned short acquireSpectra(enum e_radiometer spectrumType, enum e_entrance entranceType, unsigned short vnirIntegrationTime_ms,
				unsigned short swirIntegrationTime_ms, unsigned short scanCount, unsigned short seriesMaxDuration_s, s_spectrum_dataset *pSpectraTarget);

		/**
		 * \brief	Sets verbosity of this driver.
		 * \param	loglevel verbosity level
		 */
		void setLoglevel(e_loglevel loglevel);

		/**
		 * \brief	sets SWIR module thermal control setpoint
		 * \param float target temperature in 'C, must be in range [-15..40]
		 * \return status of execution: True if successful, false if not.
		 */
		bool setTECSetpoint(float setpoint_C);

		/**
		 * \brief	shuts down SWIR module thermal controller
		 * \return status of execution: True if successful, false if not.
		 */
		bool shutdown_TEC(void);

		/**
		 * \brief	reboot the instrument
		 * \return status of execution: True if successful (BOOTED packet got in response), false if not.
		 */
		bool reboot(void);

		/********************* UNSAFE! THESE CAN BRICK YOUR INSTRUMENT IF YOU TRY REAL HARD! **********************/

		/**
		 * \brief	Enters unsafe mode, in which instrument accepts firmware and calibration coefficient updates
		 * To exit this mode instrument needs to be rebooted
		 * \return status of execution: True if successful, false if not.
		 */
		bool enterFlashWriteMode(void);

		/**
		 * \brief	Sends extended calibration coefficients to the instrument.
		 * Must be called in flash write mode.
		 * \param pNewExternalCalibrationCoeficients pointer to structure with new coefficients to be saved.
		 * \return status of execution: True if successful, false if not.
		 */
		bool sendCalibrationCoefficients(s_extended_calibration_coefficients *pNewExternalCalibrationCoeficients);

		/**
		 * \brief	Saves previously sent extended calibration coefficients to the instrument flash.
		 * Must be called in flash write mode.
		 * \return status of execution: True if successful, false if not.
		 */
		bool saveCalibrationCoefficients(void);

		/**
		 * \brief	Fills firmware_info structure.
		 * \return status of execution: True if successful, false if not.
		 */
		bool getFirmwareInfo(void);
		/**
		 * \brief	Sends new firmware data to the instrument.
		 * Must be called in flash write mode.
		 * \param filePath path to the binary file to send to the instrument
		 * \return status of execution: True if successful, false if not.
		 */
		bool sendNewFirmwareData(std::string filePath);

		/**
		 * \brief	Checks for dataset checksum and aves previously sent new firmware binary image to the instrument flash.
		 * Must be called in flash write mode.
		 * \return status of execution: True if successful, false if not.
		 */
		bool saveNewFirmwareData(void);

		/**
		 * \brief	Switches default firmware slot to boot into and reboots
		 * Must be called in flash write mode.
		 * \return status of execution: True if successful, false if not.
		 */
		bool switchFirmwareSlot(void);

		/* General information about the instrument */
		struct s_booted hw_info;
		struct s_firwmare_info firmware_info;

		/* Hardware availability on this particular unit*/
		struct s_available_hardware available_hardware;
		/* Basic calibration coefficients, required for running (pixel to wavelength mapping, non-linearity compensation, etc) */
		struct s_calibration_coefficients_unpacked calibration_coefficients_basic;
		/* Advanced calibration coefficients, necessary for uncertainty evaluation */
		struct s_extended_calibration_coefficients extended_calibration_coefficients;

		static std::vector<s_hypstar_instance> instance_holder;
	private:
		Hypstar(std::string portname);

		bool sendCmd(unsigned char cmd, unsigned char * pParameters, unsigned short paramLength);
		bool sendCmd(unsigned char cmd);
		bool sendAndWaitForAcknowledge(unsigned char cmd, unsigned char * pPacketParams, unsigned short packetParamLength, const char * pCommandNameString);
		bool waitForDone(unsigned char cmd, const char * pCommandNameString, float timeout_s);
		bool sendAndWaitForDone(unsigned char cmd, unsigned char* pPacketParams, unsigned short paramLength, const char* pCommandNameString, float timeout_s = 1);
		bool sendAndWaitForAckAndDone(unsigned char cmd, unsigned char * pPacketParams, unsigned short paramLength, const char * pCommandNameString, float timeout_s);
		int readData(float timeout_s = READTIMEOUT);
		int exchange(unsigned char cmd, unsigned char * pPacketParams, unsigned short paramLength, const char * pCommandNameString, float timeout_s = 0.5);
		int getPacketedData(char cmd, unsigned char * pPacketParams, unsigned short paramLength, unsigned char * pTargetMemory, const char * pCommandNameString);
		bool sendPacketedData(const char commandId, unsigned char * pDataSet, int datasetLength, const char *pCommandIdtring);
		void outputStream(FILE *stream, const char * type, const char* fmt, ...);
		int findInstrumentBaudrate(int expectedBaudrate);
		void logBinPacket(const char * direction, unsigned char * pPacket, int packetLength);
		void logBytesRead(int rx_count, const char * expectedCommand, const char * pCommandNameString);
		void outputLog(e_loglevel level, const char* level_string, FILE *stream, const char* fmt, ...);
		linuxserial *hnport; //serial port object
		unsigned char rxbuf[RX_BUFFER_PLUS_CRC32_SIZE];
		e_loglevel _loglevel = ERROR;
		unsigned short lastCaptureLongestIntegrationTime_ms;
};

std::vector<Hypstar::s_hypstar_instance> Hypstar::instance_holder;

#define REQUEST(x) exchange(x, NULL, 0, #x)
#define EXCHANGE(x, y, z) exchange(x, y, z, #x)
#define GET_PACKETED_DATA(x, y, z, q) getPacketedData(x, y, z, q, #x)
#define SEND_AND_WAIT_FOR_ACK(x, y, z) sendAndWaitForAcknowledge(x, y, z, #x)
#define SEND_AND_WAIT_FOR_DONE(x, y, z) sendAndWaitForDone(x, y, z, #x)
#define WAIT_FOR_DONE(x, y) waitForDone(x, #x, y)
#define SEND_AND_WAIT_FOR_ACK_AND_DONE(x, y, z, q) sendAndWaitForAckAndDone(x, y, z, #x, q)
#define SEND_PACKETED_DATA(x, y, z) sendPacketedData(x, y, z, #x)

// Wrapper for interfacing with C or Python via ctypes
extern "C"
{
	struct hs_object_holder;
	typedef struct hs_object_holder hypstar_t;

	hypstar_t *hypstar_init(const char *port);
	void hypstar_close(hypstar_t *hs);

	bool hypstar_set_baudrate(hypstar_t *hs, e_baudrate new_baudrate);
	uint64_t hypstar_get_time(hypstar_t *hs);
	bool hypstar_set_time(hypstar_t *hs, uint64_t time);
	void hypstar_set_loglevel(hypstar_t *hs, e_loglevel loglevel);
	bool hypstar_get_hw_info(hypstar_t *hs, s_booted *target);
	bool hypstar_get_env_log(hypstar_t *hs, unsigned char index, s_environment_log_entry *target);
	bool hypstar_get_calibration_coefficients_basic(hypstar_t *hs, s_calibration_coefficients_unpacked *coef_target);
	bool hypstar_get_calibration_coefficients_extended(hypstar_t *hs, s_extended_calibration_coefficients *ext_cal_coef_target);
	bool hypstar_get_calibration_coefficients_all(hypstar_t *hs, s_calibration_coefficients_unpacked *coef_target, s_extended_calibration_coefficients *ext_cal_coef_target);
	unsigned short hypstar_capture_spectra(hypstar_t *hs, enum e_radiometer spec, enum e_entrance mux,
	unsigned short vnir_inttime_ms, unsigned short swir_inttime_ms, unsigned short scan_count, unsigned short series_time_s);
	unsigned short hypstar_get_last_capture_memory_slots(hypstar_t *hs, unsigned short *target, unsigned short number_of_captures);
	unsigned short hypstar_download_spectra(hypstar_t *hs, unsigned short *memory_slots, unsigned short number_of_captures, s_spectrum_dataset *target);
	unsigned short hypstar_acquire_spectra(hypstar_t *hs, enum e_radiometer spec, enum e_entrance mux,
	unsigned short vnir_inttime_ms,	unsigned short swir_inttime_ms,	unsigned short scan_count, unsigned short series_time_s, s_spectrum_dataset *target);
	unsigned short hypstar_capture_JPEG_image(hypstar_t *hs, bool flip, bool mirror, bool auto_focus);
	unsigned short hypstar_download_JPEG_image(hypstar_t *hs, s_img_data_holder *target);
	bool hypstar_set_TEC_target_temperature(hypstar_t *hs, float target_temp_deg_C);
	bool hypstar_shutdown_TEC(hypstar_t *hs);
	bool hypstar_reboot(hypstar_t *hs);
	bool hypstar_enter_flash_write_mode(hypstar_t *hs);
	bool hypstar_send_calibration_coefficients(hypstar_t *hs, s_extended_calibration_coefficients *pNewExternalCalibrationCoeficients);
	bool hypstar_save_calibration_coefficients(hypstar_t *hs);
	bool hypstar_test_callback(hypstar_t *hs, void(*cb_function)(s_automatic_integration_time_adjustment_status *), int paramA, int paramB);
}

#endif // include guard
