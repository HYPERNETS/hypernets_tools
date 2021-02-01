#!/usr/bin/bash

set -o nounset
set -euo pipefail

sudo pacman -Sy python-pip tk
pip uninstall serial
pip install crcmod pyftdi yoctopuce pyserial
pip install matplotlib
# Get Access to  /dev/ttySx without 'sudo'
sudo usermod -a -G uucp $USER
# Ensure relogin
# reboot
