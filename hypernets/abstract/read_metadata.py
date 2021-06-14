#!/usr/bin/python3

"""
This is an example to give an idea on how to read a metadata.txt file provided
in a hypernets data sequence.
"""

if __name__ == '__main__':
    from configparser import ConfigParser
    # "This module provides the ConfigParser class which implements a basic
    # configuration language which provides a structure similar to what’s found
    # in Microsoft Windows INI files."
    # doc : https://docs.python.org/3/library/configparser.html

    # Create configparser object and open the file
    metadata = ConfigParser()
    metadata.read("metadata.txt")

    # Case 1 : I already know a section name and a field ----------------------
    print("Asked pan-tilt for the image is :")
    print(metadata["01_015_0090_2_0180"]["pt_ask"])  # type : str

    # Case 2 : I already know a section name ----------------------------------
    # I make a dict from the parser according to the section name :
    headerMetadata = dict(metadata["Metadata"])
    # Then I read the dictionary
    for field, value in headerMetadata.items():
        print("%s is %s" % (field, value))

    # Case 3 : I know nothing about the file ----------------------------------
    # Loop over the section with an iterator
    for i, section in enumerate(metadata.sections()):
        print("="*80)
        print("Section %i : %s" % (i, section))

        # Same as the case 2:
        for field, value in dict(metadata[section]).items():
            print("%s is %s" % (field, value))
