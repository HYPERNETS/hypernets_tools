#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
	echo "This script should not be run as root, use $0 (whithout sudo) instead" 1>&2
	read -p "   Continue anyway (y/n) ?" -rn1
	if [[ ! $REPLY =~ ^[Yy]$ ]]; then 
		echo
		exit 1
	fi
fi


python -m pip install jupyter

jupyter notebook --generate-config
jupyter notebook password
jupyter nbextension enable --py widgetsnbextension

# Patch config file
sed -i "s/# c.NotebookApp.ip = 'localhost'/c.NotebookApp.ip = '0.0.0.0'/g"\
	~/.jupyter/jupyter_notebook_config.py

sed -i "s/# c.NotebookApp.allow_origin = ''/c.NotebookApp.allow_origin = '*'/g"\
	~/.jupyter/jupyter_notebook_config.py

# Then, try :
# jupyter notebook --no-browser

python -m pip install voila

# Try : 
# voila --no-browser installation_on_site.ipynb
