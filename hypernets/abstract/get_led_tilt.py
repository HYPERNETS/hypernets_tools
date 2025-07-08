from hypernets.abstract.protocol import Protocol
from hypernets.abstract.request import Request, InstrumentAction
from hypernets.hypstar.libhypstar.python.data_structs.spectrum_raw \
        import RadiometerEntranceType
from hypernets.abstract.geometry import Geometry
from configparser import ConfigParser
import sys

if __name__ == '__main__':
    config = ConfigParser()
    config.read('config_dynamic.ini')
    
    ## look for VM measurement in all sequence files
    expected_keys = ['sequence_file_sched2', 'sequence_file_alt', 
                     'sequence_file_sched1', 'sequence_file', 
                     'sequence_file_sched3']
    values = {}
    
    ## get file names from config_dynamic.ini
    if config.has_section('general'):
        for key in expected_keys:
            value = config.get('general', key, fallback=None)
            if value is not None:
                values[key] = value
    
    if not values:
        print(f"No sequence file names found in config_dynamic.ini")
        exit(-1)
    
    ## loop through sequence files and look for VM measurements
    for key, value in values.items():
        try:
            protocol = Protocol(value)
        except FileNotFoundError as e:
            print(f"Failed to open '{key}' file '{value}' when looking for LED source tilt position", file=sys.stderr)
            continue
        except Exception as e:
            print(f"{e}", file=sys.stderr)
            print(f"Failed to read '{key}' file '{sequence_file} when looking for LED source tilt position", file=sys.stderr)
            print("Wrong syntax in sequence file?", file=sys.stderr)
            continue

        # found sequence containing VM measurement
        if protocol.check_if_vm_requested() == True:
            for i, (geometry, requests) in enumerate(protocol, start=1):
                for request in requests:
                        ## look for VM measurement with irradiance entrance
                        if request.action == InstrumentAction.VALIDATION and \
                                request.entrance == RadiometerEntranceType.IRRADIANCE:

                            geometry.get_absolute_pan_tilt()
                            #print(f"{geometry}")
                            #print(f"{request.entrance.name}")

                            ## print absolute tilt position
                            print(f"{geometry.tilt_abs}")
                            exit(0)

    print("Did not find any LED source irradiance measurements from sequence files defined in config_dynamic.ini")
    exit(-1)
