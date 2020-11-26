#!/usr/bin/bash

set -o nounset
set -euo pipefail

pip install jupyter
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
