
from hypernets import __version__
from datetime import datetime, timezone
from configparser import ConfigParser, ExtendedInterpolation
from configparser import MissingSectionHeaderError
from re import split

from logging import debug, info, warning  # noqa


def metadata_header_base(protocol_file="placeholder.csv", now=None,
                         PI="Hypernets Virtual",
                         site_name="Virtual Site"):
    if now is None:
        now = datetime.now(timezone.utc)

    return ("[Metadata]\n"
            f"datetime = {now.strftime('%Y%m%dT%H%M%S')}\n"
            f"principal_investigator = {PI}\n"
            f"site_name = {site_name}\n"
            f"protocol_filename = {protocol_file}\n")


def parse_config_metadata(sequence_file, config_file="config_dynamic.ini",
                          instrument_sn=0, vm_sn=0):
    globals()["instrument_sn"] = instrument_sn
    globals()["vm_sn"] = vm_sn
    globals()["sequence_file"] = sequence_file

    config = ConfigParser(interpolation=ExtendedInterpolation())

    try:
        config.read(config_file)
        metadata_section = config["metadata"]

    except (MissingSectionHeaderError, KeyError) as e:
        warning(f"{config_file} not found or no section {e}")
        str_metadata = metadata_header_base()
        return str_metadata

    # copy user-defined metadata from config file
    str_metadata = "[Metadata]\n"
    for field in metadata_section.keys():
        str_metadata += f"{field} = {metadata_section[field]}\n"

    # populate auto-generated metadata
    str_metadata += f"hypernets_tools_version = {__version__}\n"
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    str_metadata += f"datetime = {now}\n"
    str_metadata += f"hypstar_sn = {instrument_sn}\n"
    str_metadata += f"led_sn = {vm_sn}\n"
    str_metadata += f"protocol_file_name = {sequence_file}\n"

    # populate metadata from other config file sections
    meta_fields = {"latitude": "GPS:latitude", "longitude": "GPS:longitude", 
                   "offset_pan": "pantilt:offset_pan", "offset_tilt": "pantilt:offset_tilt",
                   "azimuth_switch": "pantilt:azimuth_switch"}

    for key in meta_fields:
        try:
            conf_sec, conf_parm = split(":", meta_fields[key])
            str_metadata += f"{key} = {config[conf_sec][conf_parm]}\n"

        except (KeyError) as e:
            warning(f"{e} not found in '{config_file}' while parsing '{meta_fields[key]}'")

    return str_metadata



if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-f", "--filename", type=str, required=True,
                        help="Select a protocol file (txt, csv)")

    from logging import basicConfig, DEBUG
    log_fmt = '[%(levelname)-7s %(asctime)s] (%(module)s) %(message)s'
    dt_fmt = '%H:%M:%S'
    basicConfig(level=DEBUG, format=log_fmt, datefmt=dt_fmt)
    args = parser.parse_args()
    info("\n" + parse_config_metadata(args.filename))
