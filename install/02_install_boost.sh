#!/usr/bin/bash
pacman -Sy gcc
wget https://dl.bintray.com/boostorg/release/1.71.0/source/boost_1_71_0.zip 
unzip boost_1_71_0.zip
cd boost_1_71_0/
./bootstrap.sh
sudo ./b2 install
# Add the library path to env
sudo echo 'LD_LIBRARY_PATH="/usr/local/lib"' >> /etc/environment
