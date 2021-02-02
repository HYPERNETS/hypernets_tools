

from configparser import ConfigParser
from hypernets.virtual.read_metadata import metadata_header


def parse_config_metadata(config):
    # TODO
    pass


def read_config_file(config_file="config_hypernets.ini"):
    """
    Not implemented yet
    """

    config = ConfigParser()
    config.read(config_file)

    try:
        metadata_section = config["metadata"]
        parse_config_metadata(metadata_section)

    except KeyError:
        # FIXME need refactoring
        print(f"Warning : no 'metadata' section in {config_file}.")
        return metadata_header()

    return True


if __name__ == '__main__':
    # TODO : from argparse import ArgumentParser
    if not read_config_file():
        from datetime import datetime
        print(metadata_header(now=datetime.utcnow(),
                              protocol_file="proto.csv"))
