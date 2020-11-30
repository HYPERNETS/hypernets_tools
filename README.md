![Hypernets Logo](hypernets/resources/logo.png)
  
  
## Instructions :
First download this repository (as a zip file under the tab *code*) or using
*git clone*.
  
After unzipping (or clone), go to the folder *hypernets_tools-main* and edit
the *config_hypernets.ini* according to your configuration. The most important
section is *yoctopuce*. 

## Prerequisite : 
### Installing Boost v1.71 (~1h)
> cd hypernets/install  
> sudo bash 02_install_boost.sh
   
   
## Optional :
### Jupyter Notebook
If you want to connect (ssh or python) on the host system from any web browser via wifi, 
install first *jupyter notebook* :

> cd hypernets/install  
> bash 03_install_jupyter.sh

You can then launch the notebook :
> jupyter notebook 

And should be able (once Wi-Fi connection is up) to access the address : 
> 10.42.0.1:8888
