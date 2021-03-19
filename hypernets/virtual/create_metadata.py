
from hypernets import __version__
from datetime import datetime
from configparser import ConfigParser, ExtendedInterpolation
from configparser import MissingSectionHeaderError

# TODO : Dump data from pickle for lat:lon


def special_value(value):
    if value == "{datetime}":
        return datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    elif value == "{v_hypernets_tools}":
        return __version__
    else:
        return "N/A"


def metadata_header_base(protocol_file="placeholder.csv", now=None,
                         PI="Hypernets Virtual",
                         site_name="Virtual Site"):
    if now is None:
        from datetime import datetime
        now = datetime.utcnow()

    return ("[Metadata]\n"
            f"datetime = {now.strftime('%Y%m%dT%H%M%S')}\n"
            f"principal_investigator = {PI}\n"
            f"site_name = {site_name}\n"
            f"protocol_filename = {protocol_file}\n")


def parse_config_metadata(config_file="config_hypernets.ini"):

    config = ConfigParser(interpolation=ExtendedInterpolation())

    try:
        config.read(config_file)
        metadata_section = config["metadata"]

    except (MissingSectionHeaderError, KeyError) as e:
        print(f"Warning : {config_file} not found or no section {e}")
        str_metadata = metadata_header_base()
        return str_metadata

    str_metadata = "[Metadata]\n"
    for field in metadata_section.keys():
        if '{' and '}' in metadata_section[field]:
            special = special_value(metadata_section[field])
            str_metadata += f"{field} = {special}\n"
        else:
            str_metadata += f"{field} = {metadata_section[field]}\n"
    return str_metadata


def create_metadata():
    pass


if __name__ == '__main__':
    print(parse_config_metadata())
