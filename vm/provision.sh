#!/usr/bin/env bash
# Sets up the freshly installed VM for theme tests.
#
# Runs over SSH in the guest and is idempotent - running it several times
# does no harm. Called after build-vm.sh, before the 'clean' snapshot.

set -euo pipefail
VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/lab.env"

IP=$("$VM_DIR/vmctl.sh" ip)
echo "Provisioning $VM_NAME ($IP)..."

ssh $SSH_OPTS "$VM_USER@$IP" 'sudo bash -s' <<'GUEST'
set -euo pipefail

echo "== Detecting the login manager =="
# Fedora 44 replaced SDDM with the Plasma Login Manager. Which one
# is present decides where autologin is configured - and
# whether an SDDM theme in the tested project has any effect at all.
DM="none"
if [ -f /usr/lib/systemd/system/plasmalogin.service ]; then
    DM="plasmalogin"
    mkdir -p /etc/plasmalogin.conf.d
    cat > /etc/plasmalogin.conf.d/10-autologin.conf <<'EOF'
[Autologin]
User=tester
Session=plasma.desktop
Relogin=true
EOF
    systemctl enable plasmalogin.service
elif [ -f /usr/lib/systemd/system/sddm.service ]; then
    DM="sddm"
    mkdir -p /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/10-autologin.conf <<'EOF'
[Autologin]
User=tester
Session=plasma
Relogin=true
EOF
    systemctl enable sddm.service
fi
echo "Login manager: $DM"
echo "$DM" > /etc/plasma-lab-dm
systemctl set-default graphical.target

echo "== Disabling the first-run wizards =="
# Fedora 44 ships plasma-setup - a welcome wizard that
# runs as a session of its own BEFORE login and waits for a click. It
# thereby holds up the autologin, and without a logged-in session there is
# nothing a theme could be tested against.
systemctl disable --now plasma-setup.service 2>/dev/null || true

# plasma-welcome runs after login and puts a window over the
# desktop - that spoils every screenshot comparison.
mkdir -p /home/tester/.config
cat > /home/tester/.config/plasma-welcomerc <<'EOF'
[General]
LastSeenVersion=99.99.99
EOF
chown tester:tester /home/tester/.config/plasma-welcomerc

echo "== Updating the system =="
# Not optional: Fedora 44 GA has an ABI-incompatible combination of
# kwin and kscreenlocker with which kwin_wayland does not start. Without a
# compositor there is no Plasma session - and so nothing to test.
dnf upgrade -y 2>&1 | tail -5

echo "== Installing test tools =="
# Tools that the theme test harness needs and that are not part of
# the KDE default group.
dnf install -y --setopt=install_weak_deps=False \
    libxml2 ImageMagick python3-pip xorg-x11-server-Xvfb \
    qt6-qtdeclarative-devel appstream 2>&1 | tail -3 || true
pip install --quiet --root-user-action=ignore check-jsonschema reuse 2>&1 | tail -2 || true

echo "== Disabling screen lock and power saving =="
# In a test VM both are harmful: after a few minutes of idling
# 'virsh screenshot' only returns "Display output is not active" or
# the lock screen - an automated test run then collects black
# images and still reports success.
sudo -u tester bash <<'USERCFG'
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
# Plasma 6 reads powerdevilrc, no longer powermanagementprofilesrc (the
# VM dimmed and locked anyway until 21.10.2026).
for p in AC Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key DimDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key TurnOffDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group SuspendAndShutdown --key AutoSuspendAction 0
done
USERCFG

echo "== Saving the reference =="
# The unmodified Breeze state. With it you can check at any time
# what a theme installer has changed on the system.
mkdir -p /var/lib/plasma-lab
for f in plasmarc kdeglobals kwinrc ksplashrc; do
    cp -a "/home/tester/.config/$f" "/var/lib/plasma-lab/ref-$f" 2>/dev/null || true
done
rpm -qa --qf '%{NAME}\n' | sort > /var/lib/plasma-lab/ref-packages.txt

echo "== Versions =="
plasmashell --version 2>/dev/null || true
kwin_wayland --version 2>/dev/null || true
GUEST

echo
echo "== Cross-check: KDE tools in the guest =="
ssh $SSH_OPTS "$VM_USER@$IP" 'for t in plasma-apply-desktoptheme plasma-apply-lookandfeel \
    plasma-apply-colorscheme kpackagetool6 kwriteconfig6 kreadconfig6 plasmawindowed \
    kwin_wayland spectacle xmllint check-jsonschema reuse; do
        printf "%-28s %s\n" "$t" "$(command -v $t || echo MISSING)"
    done'

echo
echo "Provisioning done. Now save with:"
echo "  $VM_DIR/vmctl.sh snap create clean"
