#!/usr/bin/env bash
# Sets up the Ubuntu VM for theme tests - or catches up on it.
#
#   ./ubuntu-provision.sh
#
# Normally cloud-init does this on first boot (ubuntu-lab.user-data).
# This script repeats the same steps over SSH and is idempotent.
# It became necessary on the first build on 07.10.2026: Docker had set the
# host's FORWARD policy to DROP, the VM could not reach the network, and
# cloud-init aborted the package installation but still set up the rest
# (marker set, cloud-init disabled afterwards). Without this script
# the only option was a complete rebuild.

set -euo pipefail
VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/ubuntu.env"

IP=$(LAB_ENV=ubuntu.env "$VM_DIR/vmctl.sh" ip)
echo "Provisioning $VM_NAME ($IP)..."

ssh $SSH_OPTS "$VM_USER@$IP" 'sudo bash -s' <<'GUEST'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "== Packages =="
timeout 20 curl -s -o /dev/null http://archive.ubuntu.com/ubuntu/ \
    || { echo "ERROR: no network in the VM (Docker FORWARD DROP on the host?)"; exit 1; }
apt-get update -q
apt-get -y -q full-upgrade
apt-get -y -q install qemu-guest-agent kubuntu-desktop language-pack-kde-de \
    libxml2-utils imagemagick rsync
systemctl enable --now qemu-guest-agent

echo "== Autologin =="
# Can only be decided AFTER kubuntu-desktop - before that there is no login manager.
rm -f /etc/sddm.conf.d/10-autologin.conf /etc/plasmalogin.conf.d/10-autologin.conf
if [ -f /usr/lib/systemd/system/plasmalogin.service ]; then
    mkdir -p /etc/plasmalogin.conf.d
    printf '[Autologin]\nUser=tester\nSession=plasma\nRelogin=true\n' > /etc/plasmalogin.conf.d/10-autologin.conf
    echo plasmalogin > /etc/plasma-lab-dm
else
    # 99, not 10: Kubuntu ships 20-kubuntu.conf with an empty
    # [Autologin] User= - SDDM reads alphabetically, the later one wins.
    mkdir -p /etc/sddm.conf.d
    printf '[Autologin]\nUser=tester\nSession=plasma\nRelogin=true\n' > /etc/sddm.conf.d/99-plasma-lab-autologin.conf
    echo sddm > /etc/plasma-lab-dm
fi
echo "Login manager: $(cat /etc/plasma-lab-dm)"
systemctl set-default graphical.target

echo "== GRUB as on a desktop installation =="
rm -f /etc/default/grub.d/50-cloudimg-settings.cfg
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/; s/^GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/; s/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub
update-grub 2>&1 | tail -1
update-initramfs -u 2>&1 | tail -1

echo "== Screen lock, power saving, welcome window off =="
sudo -u tester bash <<'USERCFG'
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
# Plasma 6 reads powerdevilrc, no longer powermanagementprofilesrc.
# There a timeout of 0 means "immediately", not "never" - with the old
# keys the screen went off right after login.
for p in AC Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key DimDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key TurnOffDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group SuspendAndShutdown --key AutoSuspendAction 0
done
mkdir -p ~/.config
printf '[General]\nLastSeenVersion=99.99.99\n' > ~/.config/plasma-welcomerc
USERCFG

echo "== Reference =="
mkdir -p /var/lib/plasma-lab
dpkg-query -W -f '${Package}\n' | sort > /var/lib/plasma-lab/ref-packages.txt
touch /etc/cloud/cloud-init.disabled /etc/plasma-lab-ready
GUEST

echo
echo "Done. Reboot so that Plasma comes up with autologin:"
echo "  LAB_ENV=ubuntu.env ./vmctl.sh ssh 'sudo reboot'"
