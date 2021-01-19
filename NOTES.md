# Notes

## TODO : 

### Software Watchdog 
* to ensure shutting down before power-cycling
* should be an option in the config file 

### Virtual environments for the application
* Avoid python update issues
* pipenv for example
* Use of requirements.txt
 

## New Ideas : 

### Add a metadata header section in config_hypernets.ini 
from where we can grab all informations to put in metadata.txt of each SEQ.

Example : 

[Metadata Header]
PI = LOV<br />
site_name = Villefranche<br />
SN_Hypstar = {serial_instrument}<br />
FW_Hypstar = {fw_instrument}<br />
datetime = {datetime}<br />
protocol = {protocol_file_name}<br />
comments = First Test in Villefranche<br />

Where {variable} are parsed by the protocol reader.

### Config checker before field deployment
* A short script that check basics before deployment
* Network check
* Required / Optional fields in config file
* Valid protocol
* ...

### Async Download Data
* While the pan-tilt is moving to the next position
* At the end of the sequence
* Using Threads ?

### Bind useful configuration port using auto-ssh
* Forward of ssh
* Forward of jupyter
* Forward of Yoctopuce Config page
* Security Issues ?
