#ifndef LIBHYPSTAR_TYPEDEFS_H
#define LIBHYPSTAR_TYPEDEFS_H

#include <cstring>

#define DEFAULT_BAUD_RATE 115200
#define RX_BUFFER_SIZE 1024
#define CMD_SIZE 1
#define PACKET_LEN_SIZE 2
#define PACKET_HEADER_SIZE (CMD_SIZE + PACKET_LEN_SIZE) // 1 + 2 = 3
#define PACKET_CRC_SIZE 1
#define PACKET_DECORATORS_TOTAL_SIZE (PACKET_HEADER_SIZE + PACKET_CRC_SIZE) // 3 + 1 = 4
#define DATA_PACKET_ID_LEN_SIZE 4
#define PACKET_BODY_SIZE_MAX (RX_BUFFER_SIZE - PACKET_DECORATORS_TOTAL_SIZE) // 1024 - 4 = 1020
#define DATA_PACKET_BODY_SIZE_MAX (PACKET_BODY_SIZE_MAX - DATA_PACKET_ID_LEN_SIZE) // 1020 - 4 = 1016
#define DATA_PACKET_DECORATOR_SIZE (PACKET_DECORATORS_TOTAL_SIZE + DATA_PACKET_ID_LEN_SIZE) // 4 + 4 = 8
#define RX_BUFFER_PLUS_CRC32_SIZE (RX_BUFFER_SIZE + 4)

#define MAX_IMG_W 2592
#define MAX_IMG_H 1944

#define MAX_SPEC_LENGTH 2048

#define MIN_TEC_SETPOINT -15.0
#define MAX_TEC_SETPOINT 40.0
#define TEC_OFF -100.0

// capture timeout multiplier
#define CAPTURE_TIMEOUT_MULT 1.2
// capture timeout addition (seconds) to each capture (mainly for SWIR overhead on 115kbps serial)
#define CAPTURE_TIMEOUT_ADD_EACH 0.2
// capture timeout addition (seconds; has to be long enough for changing MUX position)
#define CAPTURE_TIMEOUT_ADD 5.0

// default image capture timeout in seconds
#define DEFAULT_IMG_TIMEOUT 10.0

// cmd retry count
#define CMD_RETRY 5

// calibration commands 0x2?
#define GET_CAL_COEF 0x21
#define SET_CAL_COEF 0x22
#define SAVE_CAL_COEF 0x23

// secondary data commands 0x3?
#define GET_ENV 0x32
#define GET_LOG 0x33

// thermal control commands 0x4?
#define SET_SWIR_TEMP 0x41

// spectrometer control commands 0x5?
#define CAPTURE_SPEC 0x51
#define GET_SPEC 0x52
#define GET_SLOTS 0x53

// camera control commands 0x6?
#define CAPTURE_MM_IMG 0x61
#define GET_MM_IMG 0x62

// system control commands 0x9?
#define GET_FW_VER 0x91
#define ENTER_FLASH_WRITE_MODE 0x92
#define BOOT_NEW_FW 0x93
#define SAVE_NEW_FW 0x94
#define GET_SYSTIME 0x95
#define SET_SYSTIME 0x96
#define ABORT_TASK 0x97
#define REBOOT 0x98
#define SHUTDOWN 0x99
#define SET_BAUD 0x9A

// general command parser error codes 0x9?
#define PARM_OUT_OF_RANGE 0x9B
#define HW_NA 0x9C
#define BAD_STATE 0x9D
#define MISSING_PARMS 0x9E

// capture spectra command parser error codes 0xA?
#define WRONG_SPEC 0xA1
#define WRONG_OPTICS 0xA2
#define NO_LIMIT 0xA4
#define INT_TOO_LONG 0xA5
#define SEQ_TOO_LONG 0xA6

// capture image command parser error codes 0xB?
#define BAD_IMG_TYPE 0xB0
#define BAD_RESOLUTION 0xB1

// data packet identifiers 0xB?
#define SPEC_DATA 0xB1
#define IMG_DATA 0xB2
#define LOG_DATA 0xB3
#define SLOT_DATA 0xB5
#define ENV_DATA 0xBE
#define FW_DATA 0xBF

// status packets 0xC?
#define AUTOINT_STATUS 0xC8
#define RESEND 0xC9
#define ACK 0xCA
#define BOOTED 0xCB
#define CAL_COEFS 0xCC
#define DONE 0xCD
#define NAK 0xCE

// VM control commands 0xD?
#define VM_ON 0xD0
#define SEL_VM_SRC 0xD1
#define VM_SRC_ON 0xD2
#define CAPTURE_VM_IMG 0xD8

#define GET_VM_IMG 0xD9
#define PASS_TO_VM 0xDA

// error codes 0xE?
#define BAD_CRC 0xE0
#define BAD_LENGTH 0xE1
#define BAD_PARM 0xE2
#define TOO_SHORT 0xE4
#define NOT_IMPLEMENTED 0x9A

class eHypstar {};
class eBadRx: public eHypstar {};
class eBadLength: public eBadRx {};
class eBadRxCRC: public eBadRx {};
class eBadID: public eBadRx {};
class eBadTxCRC: public eHypstar {};
class eBadResponse: public eHypstar {};
class eBadInstrumentState: public eHypstar {};

// received packet must start with one of these identifiers
const uint8_t packet_identifiers[] = {
		AUTOINT_STATUS
		,ACK
		,DONE
		,IMG_DATA
		,SPEC_DATA
		,SLOT_DATA
		,ENV_DATA
		,NAK
		,BOOTED
		,CAL_COEFS
		,LOG_DATA
		,FW_DATA
		,SAVE_NEW_FW
		,GET_FW_VER
		,GET_SYSTIME};

struct __attribute__((__packed__)) s_booted
{
	uint8_t firmware_version_major;
	uint8_t firmware_version_minor;
	uint8_t firmware_version_revision;
	uint32_t instrument_serial_number;
	uint8_t mcu_hardware_version;
	uint8_t psu_hardware_version;
	uint16_t vis_serial_number;
	uint32_t swir_serial_number;
	uint16_t memory_slot_count;
	bool vnir_module_available : 1; // LSB
	bool swir_module_available : 1;
	bool optical_multiplexer_available : 1;
	bool camera_available : 1;
	bool accelerometer_available : 1;
	bool humidity_sensor_available : 1;
	bool pressure_sensor_available : 1;
	bool swir_tec_module_available : 1;
	bool sd_card_available : 1;
	bool power_monitor_1_available: 1;
	bool power_monitor_2_available: 1;
};

struct __attribute__((__packed__)) s_firwmare_info {
	uint8_t 	firmware_version_major;
	uint8_t 	firmware_version_minor;
	uint8_t 	firmware_version_revision;
	uint8_t		current_flash_slot;
	uint8_t		is_semolator_mode;	// debug info, should be 0
	uint8_t 	mcu_hardware_version;
	uint8_t 	psu_hardware_version;
};

struct s_available_hardware
{
	bool vnir_module;
	bool swir_module;
	bool optical_multiplexer;
	bool camera;
	bool accelerometer;
	bool humidity_sensor;
	bool pressure_sensor;
	bool swir_tec_module;
};

struct __attribute__((__packed__)) s_calibration_coefficients_raw
{
	int8_t vnir_wavelength_coefficientss_raw[14 * 6];
	int8_t vnir_linerity_coefficients_raw[14 * 8];
	int8_t swir_wavelength_coefficients_raw[14 * 5];
	int16_t accelerometer_horizontal_reference[3];
};

struct s_calibration_coefficients_unpacked
{
	double vnir_wavelength_coefficients[6];
	double vnir_linearity_coefficients[8];
	double swir_wavelength_coefs[5];
	int16_t accelerometer_horizontal_reference[3];
};

struct __attribute__((__packed__)) s_extended_calibration_coefficients
{
	uint32_t instrument_serial_number;
	uint16_t calibration_year;
	uint8_t calibration_month;
	uint8_t calibration_day;
	int16_t accelerometer_horizontal_reference[3];
	float vnir_nonlinearity_coefficients[4];
	float vnir_coefficients_L[2048];
	float vnir_coefficients_E[2048];
	float swir_nonlinearity_coefficients[9];
	float swir_coefficients_L[256];
	float swir_coefficients_E[256];
	uint32_t crc32;
};

struct __attribute__((__packed__)) s_environment_log_entry
{
	int64_t timestamp; 						// == time_t tm, but time_t is 32 bits on 32bit system and 64 bits on 64bit system...
	int16_t humidity_sensor_temperature;	// units: 0.01 'C
	uint16_t humidity_sensor_humidity;		// units: 0.1 % relative humidity
	int32_t pressure_sensor_pressure;		// units: 0.1 mbar
	int32_t pressure_sensor_temperature;	// units: 0.01 'C
	int16_t accelerometer_readings_XYZ[3];	// ADC units
	float internal_ambient_temperature;
	float swir_body_temperature;
	float swir_heatsink_temperature;
	float energy_common_3v3;				// mWhrs of energy consumed by all the control electronics and camera on 3.3V bus since last boot
	float energy_mcu_3v3;					// mWhrs of energy consumed by all the control electronics on 3.3V bus since last boot
	float energy_camera_3v3;				// mWhrs of energy consumed by camera module on 3.3V bus since last boot
	float voltage_common_3v3;				// volts of instantaneous measurement on 3.3V shared bus
	float voltage_mcu_3v3;					// volts of instantaneous measurement on 3.3V control electronics bus
	float voltage_camera_3v3;				// volts of instantaneous measurement on 3.3V camera bus
	float current_common_3v3;				// Amperes of instantaneous measurement on 3.3V shared bus
	float current_mcu_3v3;					// Amperes of instantaneous measurement on 3.3V control electronics bus
	float current_camera_3v3;				// Amperes of instantaneous measurement on 3.3V camera bus
	float energy_swir_module_12v;			// mWhrs of energy consumed by SWIR and SWIR Thermal control (TEC) modules on 12V bussince last boot
	float energy_multiplexer_12v;			// mWhrs of energy consumed by optical multiplexer on 12V bus since last boot
	float energy_vnir_module_5v;			// mWhrs of energy consumed by VNIR module on 5V bus since last boot
	float energy_input_12v;					// mWhrs of energy consumed by the whole instrument on 12V power input bus since last boot
	float voltage_swir_module_12v;			// volts of instantaneous measurement on SWIR + SWIR TEC 12V bus
	float voltage_multiplexer_12v;			// volts of instantaneous measurement on 12V optical multiplexer shared bus
	float voltage_vnir_module_5v;			// volts of instantaneous measurement on 5V VNIR module power bus
	float voltage_input_12v;				// volts of instantaneous measurement on 12V power input bus
	float current_swir_module_12v;			// Amperes of instantaneous measurement on 12V SWIR + SWIR TEC power bus
	float current_multiplexer_12v;			// Amperes of instantaneous measurement on 12V optical multiplexer bus
	float current_vnir_module_5v;			// Amperes of instantaneous measurement on 5V VNIR module power bus
	float current_input_12v;				// Amperes of instantaneous measurement on 12V power input
};

// supported baud rates
enum e_baudrate
{
	B_115200 = 115200,
	B_460800 = 460800,
	B_921600 = 921600,
	B_3000000 = 3000000,
	B_6000000 = 6000000,
	B_8000000 = 8000000
};

// supported jpg resolutions
enum e_jpg_resolution
{
	QQVGA,
	QCIF,
	QVGA,
	WQVGA,
	CIF,
	VGA,
	WVGA,
	XGA,
	JPG_720p,
	SXGA,
	UXGA,
	JPG_1080p,
	WUXGA,
	QXGA,
	JPG_5MP					// currently supported only 5MP
};

struct __attribute__((__packed__)) s_capture_image_request_flags
{
	bool scale : 1;			// LSB of flags byte // should be 0 : if requested image size is less than 5MP, it can be scaled (1) or cropped to size (0) (akin to digital zoom)
	bool flip_v : 1;		// flip vertically
	bool mirror_h : 1;		// mirror horizontally
	bool auto_focus : 1;	// use auto focus (1) or not (0). FW versions prior to 0.14 don't support disabling auto-focus
	int8_t na : 4;  // MSB of flags byte, should be 0
};

// supported image formats
enum e_image_format
{
	TEST_MCU = 0x01,
	RAW_RGB = 0x02,
	RGB565 = 0x03,
	RGB555 = 0x04,
	RGB444 = 0x05,
	CCIR656 = 0x06,
	YUV422 = 0x07,
	YUV420 = 0x08,
	YCbCr422 = 0x09,
	TEST_CAM = 0x0A,
	JPEG = 0x0B				// currently supported only JPEG
};

struct __attribute__((__packed__)) s_capture_image_request
{
	uint8_t format;
	uint16_t resolution_h;
	uint16_t resolution_v;
	s_capture_image_request_flags flags;
};

struct __attribute__((__packed__)) s_image_data_holder_rgb565
{
	uint16_t resolution_h;
	uint16_t resolution_v;
	uint16_t image_body[MAX_IMG_W * MAX_IMG_H];
};

struct __attribute__((__packed__)) s_image_data_holder_jpeg
{
	uint16_t image_body[MAX_IMG_W * MAX_IMG_H]; // most likely jpg images are much smaller
};

struct __attribute__((__packed__)) s_img_data_holder
{
	uint8_t image_type;
	union
	{
		s_image_data_holder_jpeg image_data_jpeg;
		s_image_data_holder_rgb565 image_data_rgb565;
	};
	int image_size;
	uint32_t crc32_spaceholder; // just in case, probably unnecessary since the crc32 will be in most cases somewhere inside the image data...
};

struct __attribute__((__packed__)) s_spectrum_optical_configuration
{
	int8_t na : 3; 						// LSB, should be 0
	// Having both of these as 0 performs DARK measurement. Having both set to 1 will result in error message
	bool irradiance : 1;				// capture using radiance entrance
	bool radiance : 1;					// capture using irradiance entrance
	bool semolator_fake_saturation : 1; // should be 0, dummy used for testing
	// Enabling both captures in hyperspectral mode. Having both set to 0 will result in error message
	bool swir : 1;						// capture using SWIR module
	bool vnir : 1;						// capture using VIS module
};

struct __attribute__((__packed__)) s_capture_spectra_request_packet
{
	s_spectrum_optical_configuration capture_spectra_parameters;
	uint16_t vnir_integration_time_ms;
	uint16_t swir_integration_time_ms;
	uint16_t scan_count;
	uint16_t maximum_total_series_time_s;
};

enum e_radiometer
{
	VNIR = 0x01,
	SWIR = 0x02,
	BOTH = 0x03
};

enum e_entrance
{
	DARK = 0x00,
	RADIANCE = 0x01,
	IRRADIANCE = 0x02
};

struct __attribute__((__packed__)) s_automatic_integration_time_adjustment_status
{
	s_spectrum_optical_configuration spectrum_config;
	uint16_t current_integration_time_ms;
	uint16_t peak_adc_value;
	uint16_t next_integration_time_ms;
	uint16_t memory_slot_id;
};

struct __attribute__((__packed__)) s_acceleration_statistics_single
{
	int16_t mean_acceleration;
	int16_t standard_deviation;
};

struct __attribute__((__packed__)) s_acceleration_statistics
{
	s_acceleration_statistics_single X;
	s_acceleration_statistics_single Y;
	s_acceleration_statistics_single Z;
};

struct __attribute__((__packed__)) s_spectrum_header
{
	uint16_t dataset_total_length;
	s_spectrum_optical_configuration spectrum_config;
	int64_t timestamp_ms; // == time_t tm, but time_t is 32 bits on 32bit system and 64 bits on 64bit system...
	uint16_t integration_time_ms;
	float sensor_temperature;
	uint16_t pixel_count;
	s_acceleration_statistics acceleration_statistics;
};

struct __attribute__((__packed__)) s_spectrum_dataset
{
	s_spectrum_header spectrum_header;
	uint16_t spectrum_body[MAX_SPEC_LENGTH];
	uint32_t crc32_spaceholder; // crc32 will be here if spec_length == MAX_SPEC_LENGTH, otherwise inside spec[] array
};

class Spectrum
{
	public:
		Spectrum(){};
		Spectrum(s_spectrum_dataset *in) {
			_raw = *in;
			timestamp = _raw.spectrum_header.timestamp_ms;
			entrance = (e_entrance)((int)_raw.spectrum_header.spectrum_config.radiance | ((int)_raw.spectrum_header.spectrum_config.irradiance << 1));
			radiometer = (e_radiometer)((int)_raw.spectrum_header.spectrum_config.vnir | ((int)_raw.spectrum_header.spectrum_config.swir << 1));
			pixel_count = _raw.spectrum_header.pixel_count;
			acceleration_statistics = _raw.spectrum_header.acceleration_statistics;
			sensor_temp = _raw.spectrum_header.sensor_temperature;
			memcpy(data, _raw.spectrum_body, pixel_count);
			integration_time = _raw.spectrum_header.integration_time_ms;
		}
		int		timestamp;
		e_entrance	entrance;
		e_radiometer radiometer;
		uint16_t integration_time;
		uint16_t pixel_count;
		uint16_t data[MAX_SPEC_LENGTH];
		s_acceleration_statistics acceleration_statistics;
		float sensor_temp;

		s_spectrum_dataset* getRaw() {return &_raw;}
	private:
		s_spectrum_dataset _raw;
};

enum e_loglevel
{
	ERROR = 0,
	WARNING = 1,
	INFO = 2,
	DEBUG = 3,
	TRACE = 4			// outputs communication data
};
#endif
