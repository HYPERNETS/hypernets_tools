
from configparser import ConfigParser


def metadata_header():
    pass


def metadata_header_base(protocol_file, now=None,
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


def parse_config_metadata(now, protocol_file, serial_instrument):
    # To parse :
    # * principal_investigator
    # *
    if not read_config_file():
        return metadata_header_base()


def read_config_file(config_file="config_hypernets.ini"):
    """
    Not implemented yet
    """

    # try:
    config = ConfigParser()
    config.read(config_file)

    try:
        metadata_section = config["metadata"]
        parse_config_metadata(metadata_section)

    except KeyError:
        # FIXME need refactoring
        print(f"Warning : no 'metadata' section in {config_file}.")
        return  # metadata_header()

    return True


if __name__ == '__main__':
    # TODO : from argparse import ArgumentParser
    print(parse_config_metadata())
