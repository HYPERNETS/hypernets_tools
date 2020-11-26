#!/usr/bin/bash

set -o nounset
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root, use sudo $0 instead" 1>&2
	exit 1
fi

# OUT OF DATE
last_version_yocto="VirtualHub.linux.40924.zip"
wget "http://www.yoctopuce.com/FR/downloads/$last_version_yocto"

mkdir Yoctopuce
unzip VirtualHub.linux.40924.zip -d Yoctopuce/

# UDEV RULES :
sudo cp Yoctopuce/udev_conf/51-yoctopuce_all.rules /etc/udev/rules.d/
#1: copier binaire VirtualHub dans le répertoire /usr/sbin/
cp Yoctopuce/64bits/VirtualHub /usr/sbin
#2: vérifier que /usr/sbin/Virtualhub est exécutable :
chmod +x /usr/sbin/VirtualHub
#3: copier le fichier startup_script/yvirtualhub.service dans/etc/systemd/system/
cp Yoctopuce/startup_script/yvirtualhub.service /etc/systemd/system/
#4: vérifier que /etc/systemd/system/yvirtualhub.service est exécutable :
# chmod +x /etc/systemd/system/yvirtualhub.service
#5: recharger la configuration de systemd avec:
systemctl daemon-reload
#6:  vérifier que le script de démarrage fonctionne avec:
systemctl start yvirtualhub.service
#7: enregistrer le service pour qu'il soit démarré automatiquement
systemctl enable yvirtualhub.service
rm -rf Yoctopuce "$last_version_yocto"
#8: redémarrer la machine
# reboot
