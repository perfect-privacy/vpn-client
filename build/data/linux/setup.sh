#!/bin/bash
# setup.sh script for makeself installer

echo "Perfect Privacy Installer"

echo " Stopping Service"
service perfect-privacy stop 2>/dev/null
/opt/perfect-privacy/perfect-privacy-service daemon stop

echo " Stopping Frontend"
killall "/opt/perfect-privacy/perfect-privacy" 2>/dev/null

echo " Copying Files"
mkdir /opt/perfect-privacy    2>/dev/null
if test -f "/opt/perfect-privacy/var/storage.db"; then
  cp  /opt/perfect-privacy/var/storage.db /tmp/
fi
rm -r /opt/perfect-privacy/*
cp -ar * /opt/perfect-privacy 1>/dev/null
cp install_files/daemon/systemd/perfect-privacy.service /etc/systemd/system/

systemctl daemon-reload

echo " Installing dependency"
apt-get -y install openvpn obfs4proxy stunnel

echo " Installing Desktop Symbols"
cp    install_files/perfect-privacy.desktop /usr/share/applications/
cp -r install_files/icons/* /usr/share/icons/hicolor/
cp -r install_files/polkit/com.perfect-privacy.perfect-privacy.policy /usr/share/polkit-1/actions/
#cp install_files/man/*.gz /usr/share/man/man1/
desktop-file-install --dir=/usr/share/applications/ /usr/share/applications/perfect-privacy.desktop

if test -f "/tmp/storage.db"; then
  mv /tmp/storage.db /opt/perfect-privacy/var/
fi

echo " Restarting Service"
service perfect-privacy start
