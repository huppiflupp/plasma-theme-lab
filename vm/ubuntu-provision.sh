#!/usr/bin/env bash
# Richtet die Ubuntu-VM fuer Theme-Tests ein - oder holt es nach.
#
#   ./ubuntu-provision.sh
#
# Eigentlich erledigt das cloud-init beim ersten Start (ubuntu-lab.user-data).
# Dieses Skript wiederholt dieselben Schritte ueber SSH und ist idempotent.
# Noetig wurde es beim ersten Bau am 07.10.2026: Docker hatte die
# FORWARD-Policy des Hosts auf DROP gesetzt, die VM kam nicht ins Netz, und
# cloud-init brach die Paketinstallation ab, richtete den Rest aber trotzdem
# ein (Marker gesetzt, cloud-init danach abgeschaltet). Ohne dieses Skript
# blieb nur ein kompletter Neubau.

set -euo pipefail
VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/ubuntu.env"

IP=$(LAB_ENV=ubuntu.env "$VM_DIR/vmctl.sh" ip)
echo "Provisioniere $VM_NAME ($IP)..."

ssh $SSH_OPTS "$VM_USER@$IP" 'sudo bash -s' <<'GUEST'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "== Pakete =="
timeout 20 curl -s -o /dev/null http://archive.ubuntu.com/ubuntu/ \
    || { echo "FEHLER: kein Netz in der VM (Docker-FORWARD-DROP auf dem Host?)"; exit 1; }
apt-get update -q
apt-get -y -q full-upgrade
apt-get -y -q install qemu-guest-agent kubuntu-desktop language-pack-kde-de \
    libxml2-utils imagemagick rsync
systemctl enable --now qemu-guest-agent

echo "== Autologin =="
# Erst NACH kubuntu-desktop entscheidbar - vorher ist kein Anmeldeverwalter da.
rm -f /etc/sddm.conf.d/10-autologin.conf /etc/plasmalogin.conf.d/10-autologin.conf
if [ -f /usr/lib/systemd/system/plasmalogin.service ]; then
    mkdir -p /etc/plasmalogin.conf.d
    printf '[Autologin]\nUser=tester\nSession=plasma\nRelogin=true\n' > /etc/plasmalogin.conf.d/10-autologin.conf
    echo plasmalogin > /etc/plasma-lab-dm
else
    # 99, nicht 10: Kubuntu liefert 20-kubuntu.conf mit leerem
    # [Autologin] User= - SDDM liest alphabetisch, die spaetere gewinnt.
    mkdir -p /etc/sddm.conf.d
    printf '[Autologin]\nUser=tester\nSession=plasma\nRelogin=true\n' > /etc/sddm.conf.d/99-plasma-lab-autologin.conf
    echo sddm > /etc/plasma-lab-dm
fi
echo "Login-Manager: $(cat /etc/plasma-lab-dm)"
systemctl set-default graphical.target

echo "== GRUB wie auf einer Desktop-Installation =="
rm -f /etc/default/grub.d/50-cloudimg-settings.cfg
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/; s/^GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/; s/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub
update-grub 2>&1 | tail -1
update-initramfs -u 2>&1 | tail -1

echo "== Bildschirmsperre, Energiesparen, Willkommensfenster aus =="
sudo -u tester bash <<'USERCFG'
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
# Plasma 6 liest powerdevilrc, nicht mehr powermanagementprofilesrc.
# Dort heisst ein Zeitlimit 0 "sofort", nicht "nie" - mit den alten
# Schluesseln war der Bildschirm direkt nach dem Anmelden aus.
for p in AC Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key DimDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key TurnOffDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group SuspendAndShutdown --key AutoSuspendAction 0
done
mkdir -p ~/.config
printf '[General]\nLastSeenVersion=99.99.99\n' > ~/.config/plasma-welcomerc
USERCFG

echo "== Referenz =="
mkdir -p /var/lib/plasma-lab
dpkg-query -W -f '${Package}\n' | sort > /var/lib/plasma-lab/ref-packages.txt
touch /etc/cloud/cloud-init.disabled /etc/plasma-lab-ready
GUEST

echo
echo "Fertig. Neu starten, damit Plasma mit Autologin hochkommt:"
echo "  LAB_ENV=ubuntu.env ./vmctl.sh ssh 'sudo reboot'"
