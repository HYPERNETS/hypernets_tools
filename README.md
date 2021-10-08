![Hypernets Logo](hypernets/resources/img/logo.png)
  
## Instructions :

```sh
wget https://raw.githubusercontent.com/HYPERNETS/hypernets_tools/beta/install/EE_hypernets_installer.sh
chmod +x EE_hypernets_installer.sh
sudo ./EE_hypernets_installer.sh
```

Note : by default instrument uses baudrate of 115200. Setting instrument baud rate to higher value will reduce acquisition time, 
but instrument becomes more sensitive to electronic noise. CRC errors are reported if noise is detected on communications line.
Driver will retry command 5 times before failing. Generally we would suggest trying higher baud rates while observing
if there are no CRC errors reported in log file. Frequent CRC errors should not be a problem unless same packet fails 5 times in a row.
Then we would suggest reducing baud rate until such failures stop. Top-end baud rate use requires shielded cabling.


## New set of commands :

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
