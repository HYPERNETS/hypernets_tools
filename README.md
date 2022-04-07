![Hypernets Logo](hypernets/resources/img/logo.png)
  
  
  
## Instructions - for USB:
Plug the USB cable between the rugged PC and the "config port" of the Yocto-Pictor, then:

```sh
git clone https://github.com/hypernets/hypernets_tools
cd hypernets_tools
sudo ./install/EE_wizard.sh
```

You should be able to connect to the Yocto-Hub Webpage :
> localhost:4444

Update the firmware and disable the Wi-Fi (Airplane mode).



## Note about instrument baudrate :
Instrument uses baudrate of 115200. Setting instrument baud rate to higher value will reduce acquisition time, 
but instrument becomes more sensitive to electronic noise. CRC errors are reported if noise is detected on communications line.
Driver will retry command 5 times before failing. Generally we would suggest trying higher baud rates while observing
if there are no CRC errors reported in log file. Frequent CRC errors should not be a problem unless same packet fails 5 times in a row.
Then we would suggest reducing baud rate until such failures stop. Top-end baud rate use requires shielded cabling.


## New set of commands:

```sh
# Launch the GUI
python -m hypernets.gui

# Open a sequence :

# Playing with relays :
python -m hypernets.yocto.relay

# Both Visible and Short-Waved Infrared Irradiance :  
# (IT vnir : 64 ms ; IT swir : 128 ms)
python -m hypernets.hypstar.handler -r both -e irr -v 64 -w 128
# *Note : This will output 3 spectra (2 vnir + 1 swir).*

# Taking a picture :
python -m hypernets.hypstar.handler -p

```

## Wakeup Conditions :
Please refer to the Yoctopuce User Manual to set up Wakeup conditions for the system :  
http://www.yoctopuce.com/EN/products/yoctohub-wireless/doc/YHUBWLN1.usermanual.html#CHAP9SEC1


## Autonomous Mode

* First check if one sequence execution is working : 

```sh
./utils/run_sequence.sh
```

### Setup service at boot time

```sh
sudo ./install/04_setup_script_at_boot.sh
```

Try to start and watch what happens with :

```sh
sudo systemctl start hypernets-sequence
journalctl -u hypernets-sequence --follow
```


  
