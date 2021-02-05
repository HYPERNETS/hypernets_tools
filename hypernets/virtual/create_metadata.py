
from configparser import ConfigParser, ExtendedInterpolation
from configparser import MissingSectionHeaderError


def metadata_header():
    pass


def metadata_header_base(protocol_file="placeholder.csv", now=None,
                         PI="Hypernets Virtual",
                         site_name="Virtual Site"):
    if now is None:
        from datetime import datetime
        now = datetime.utcnow()

    return ("[Metadata]\n"
            f"creation_datetime={now.strftime('%Y%m%dT%H%M%S')}\n"
            f"principal investigator={PI}\n"
            f"site_name={site_name}\n"
            f"protocol_filename={protocol_file}\n")


def read_config_file(config_file="config_hypernets.ini"):

    config = ConfigParser(interpolation=ExtendedInterpolation())

    try:
        config.read(config_file)
    except MissingSectionHeaderError as e:
        print(f"Warning : {config_file} : {e} ")

    try:
        metadata_section = config["metadata"]
        # print(dir(metadata_section))
        print(list(metadata_section.keys()))
        print(list(metadata_section.values()))
        # parse_config_metadata(metadata_section)
    except KeyError:
        # FIXME need refactoring
        print(f"Warning : no 'metadata' section in {config_file}.")
        return False  # TODO : return default config instead

    return True


def parse_config_metadata():
    # To parse :
    # * principal_investigator
    # *
    if not read_config_file():
        return metadata_header_base()


if __name__ == '__main__':
    # TODO : from argparse import ArgumentParser
    parse_config_metadata()
