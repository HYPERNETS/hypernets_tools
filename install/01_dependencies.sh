#!/usr/bin/bash

set -o nounset
set -euo pipefail

sudo pacman -Sy python-pip tk
python -m pip uninstall serial
python -m pip install crcmod pyftdi yoctopuce pyserial
python -m pip install matplotlib
# Get Access to  /dev/ttySx without 'sudo'
sudo usermod -a -G uucp $USER
# Ensure relogin
# reboot
