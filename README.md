![Hypernets Logo](hypernets/resources/logo.png)
  
  
## Instructions :
First download this repository (as a zip file under the tab *code*) or using
*git clone*.
  
After unzipping (or clone), go to the folder *hypernets_tools-main* and edit
the *config_hypernets.ini* according to your configuration. The most important
section is *yoctopuce*. 

## Prerequisite : 
### Installing Boost v1.71 (~1h)
You will first have to install *libboost-python* dependency, it's pretty 
straightforward but a bit long (internet connection needed) :

> cd hypernets/install  
> sudo bash 02_install_boost.sh


## New set of commands :

#### Launch the GUI : 
> python -m hypernets.gui

#### Open a sequence :
> python -m hypernets.open_sequence -df hypernets/resources/sequences_sample/sequence_file.csv

#### Playing with relays : 
> python -m hypernets.scripts.relay_command

#### Playing with the instrument (examples) :

Visible Radiance single spectra (automatic integration time) :
> python -m hypernets.scripts.call_radiometer -r vnir -e rad

Both Visible and Short-Waved Infrared Irradiance :  
(IT vnir : 64 ms ; IT swir : 128 ms)
> python -m hypernets.scripts.call_radiometer -r both -e irr -v 64 -w 128   

*Note : This will output 3 spectra (2 vnir + 1 swir).*  

Taking a picture :
> python -m hypernets.scripts.call_radiometer -p

## Autonomous Mode
### Setting up service

### Wakeup Conditions :
Please refer to the Yoctopuce User Manual to set up Wakeup conditions for the system : 
http://www.yoctopuce.com/EN/products/yoctohub-wireless/doc/YHUBWLN1.usermanual.html#CHAP9SEC1
   
   
## Optional :
### Jupyter Notebook
If you want to connect (ssh or python) on the host system from any web browser via Wi-Fi, 
you should install first *jupyter notebook* :

> cd hypernets/install  
> bash 03_install_jupyter.sh

You can then launch the notebook :
> jupyter notebook 

Then connect to the Wi-Fi hotspot of the rugged PC (from any laptop) and you should be able
to access the address :

> 10.42.0.1:8888

More information about jupyter notbook : https://jupyter.org/
