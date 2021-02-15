![Hypernets Logo](hypernets/resources/img/logo.png)
  
  
## Instructions :
First download this repository (as a zip file under the tab *code*) or using
*git clone*.
  
After unzipping (or cloning), go to the folder *hypernets_tools-main* and make
a copy of the file *config_hypernets.ini.template* that you will name *config_hypernets.ini*.
Edit the new file according to your configuration. The most important section is *yoctopuce*. 

```sh
cd hypernets_tools 
cp config_hypernets.ini.template config_hypernets.ini
mousepad config_hypernets.ini
```
If you are using Joel's script for binding instrument to /dev/radiometerX, you should be good, otherwise you should change 
in config_hypernets.ini the *hypstar_port* parameter to /dev/ttyUSBx (normally ttyUSB0).

By default instrument uses baudrate of 115200. Setting instrument baud rate to higher value will reduce acquisition time, 
but instrument becomes more sensitive to electronic noise. CRC errors are reported if noise is detected on communications line.
Driver will retry command 5 times before failing. Generally we would suggest trying higher baud rates while observing
if there are no CRC errors reported in log file. Frequent CRC errors should not be a problem unless same packet fails 5 times in a row.
Then we would suggest reducing baud rate until such failures stop. Top-end baud rate use requires shielded cabling.


Libhypstar driver is now bundled with installation, but needs to be activated and installed:
```sh
cd hypernets_tools
git submodule init
git submodule update
cd hypernets/scripts/libhypstar
make lib
sudo make install
```
This will download source code for the libhypstar, compile it and copy resulting binary to /usr/lib/

Updating libhypstar with latest from the github:
```sh
cd hypernets_tools/hypernets/scripts/libhypstar
git checkout main
git pull
make lib
sudo make install
```

## New set of commands :

```sh
# Launch the GUI
python -m hypernets.gui

# Open a sequence :
python -m hypernets.open_sequence -df hypernets/resources/sequences_sample/sequence_file.csv

# Playing with relays :
python -m hypernets.scripts.relay_command

# Playing with the instrument (examples) :
# Visible Radiance single spectra (automatic integration time) :
python -m hypernets.scripts.call_radiometer -r vnir -e rad

# Both Visible and Short-Waved Infrared Irradiance :  
# (IT vnir : 64 ms ; IT swir : 128 ms)
python -m hypernets.scripts.call_radiometer -r both -e irr -v 64 -w 128   
# *Note : This will output 3 spectra (2 vnir + 1 swir).*

# Taking a picture :
python -m hypernets.scripts.call_radiometer -p

```

  

## Autonomous Mode

* First check if one sequence execution is working : 

```sh
python -m hypernets.open_sequence -df hypernets/resources/sequences_sample/sequence_file.csv
```

* Then edit "[general]" section of your configuration file according to desired settings and
test it with :
```sh
bash run_service.sh
```

### Setup service at boot time
Copy the template of the service in */etc/systemd/system* and edit it :
```sh
sudo cp install/hypernets-sequence.service /etc/systemd/system
sudo nano /etc/systemd/system/hypernets.sequence.service 
```

* *User=your_username*
* *ExecStart=*/path/to/hypernets_tools/run_service.sh*
* *WorkingDirectory=/path/to/hypernets_tools*

Try to start and watch what happens with :

```sh
sudo systemctl start hypernets-sequence
journalctl -u hypernets-sequence --follow
```

If everything works as you expect, then enable the service with : 

```sh
sudo systemctl enable hypernets-sequence
```


### Wakeup Conditions :
Please refer to the Yoctopuce User Manual to set up Wakeup conditions for the system :  
http://www.yoctopuce.com/EN/products/yoctohub-wireless/doc/YHUBWLN1.usermanual.html#CHAP9SEC1
   
   
## Optional :
### Jupyter Notebook
If you want to connect (ssh or python) on the host system from any web browser via Wi-Fi, 
you should install first *jupyter notebook* :

```sh
cd hypernets/install  
bash 03_install_jupyter.sh
```

You can then launch the notebook :

```sh
jupyter notebook --no-browser
```

Then connect to the Wi-Fi hotspot of the rugged PC (from any laptop) and you should be able
to access the address :

> 10.42.0.1:8888

More information about jupyter notbook : https://jupyter.org/

### Helpful *(draft!)* webpage for field deployment :
From documentation : *Voilà allows you to convert a Jupyter Notebook into an interactive dashboard*
(more information : https://voila.readthedocs.io/en/stable/)

ssh to the rugged pc and start *voilà* :
```sh
voila installation_on_site.ipynb --no-browser
```

Connect to the Wi-Fi hotspot of the rugged PC (from any laptop) and you should be able
to access the address :

> 10.42.0.1:8866

Notes : any comments or suggestions are welcomed here :) 
