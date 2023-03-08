#!/bin/bash
# setup.sh script for makeself installer

echo "Perfect Privacy Installer"

echo " Stopping Service"
service perfect-privacy stop 2>/dev/null

echo " Stopping Frontend"
killall "/opt/perfect-privacy/perfect-privacy" 2>/dev/null

echo " Copying Files"
mkdir /opt/perfect-privacy    2>/dev/null
cp -ar * /opt/perfect-privacy 1>/dev/null
cp install_files/daemon/systemd/perfect-privacy.service /etc/systemd/system/

systemctl daemon-reload

echho " Installing dependency"
apt-get -y install openvpn
apt-get -y install obfsproxy
apt-get -y install stunnel

echo " Installing Desktop Symbols"
cp    install_files/perfect-privacy.desktop /usr/share/applications/
cp -r install_files/icons/* /usr/share/icons/hicolor/
cp -r install_files/polkit/com.perfect-privacy.perfect-privacy.policy /usr/share/polkit-1/actions/
#cp install_files/man/*.gz /usr/share/man/man1/
desktop-file-install --dir=/usr/share/applications/ /usr/share/applications/perfect-privacy.desktop

echo " Restarting Service"
service perfect-privacy start
