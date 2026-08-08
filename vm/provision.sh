#!/usr/bin/env bash
# Richtet die frisch installierte VM fuer Theme-Tests ein.
#
# Laeuft ueber SSH im Gast und ist idempotent - mehrfaches Ausfuehren
# schadet nicht. Wird nach build-vm.sh aufgerufen, vor dem 'clean'-Snapshot.

set -euo pipefail
VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/lab.env"

IP=$("$VM_DIR/vmctl.sh" ip)
echo "Provisioniere $VM_NAME ($IP)..."

ssh $SSH_OPTS "$VM_USER@$IP" 'sudo bash -s' <<'GUEST'
set -euo pipefail

echo "== Login-Manager erkennen =="
# Fedora 44 hat SDDM durch den Plasma Login Manager ersetzt. Welcher
# vorhanden ist, entscheidet, wo das Autologin konfiguriert wird - und
# ob ein SDDM-Theme im getesteten Projekt ueberhaupt eine Wirkung hat.
DM="keiner"
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
echo "Login-Manager: $DM"
echo "$DM" > /etc/plasma-lab-dm
systemctl set-default graphical.target

echo "== Ersteinrichtungsassistenten abschalten =="
# Fedora 44 liefert plasma-setup mit - einen Willkommensassistenten, der
# als eigene Sitzung VOR dem Login laeuft und auf einen Klick wartet. Er
# haelt damit den Autologin auf, und ohne angemeldete Sitzung gibt es
# nichts, wogegen sich ein Theme testen liesse.
systemctl disable --now plasma-setup.service 2>/dev/null || true

# plasma-welcome laeuft nach dem Anmelden und legt ein Fenster ueber den
# Desktop - das stoert jeden Screenshot-Vergleich.
mkdir -p /home/tester/.config
cat > /home/tester/.config/plasma-welcomerc <<'EOF'
[General]
LastSeenVersion=99.99.99
EOF
chown tester:tester /home/tester/.config/plasma-welcomerc

echo "== System aktualisieren =="
# Nicht optional: Fedora 44 GA hat eine ABI-inkompatible Kombination aus
# kwin und kscreenlocker, mit der kwin_wayland nicht startet. Ohne
# Compositor gibt es keine Plasma-Sitzung - und damit nichts zu testen.
dnf upgrade -y 2>&1 | tail -5

echo "== Testwerkzeuge nachinstallieren =="
# Werkzeuge, die der Theme-Testharness braucht und die in der
# KDE-Standardgruppe nicht enthalten sind.
dnf install -y --setopt=install_weak_deps=False \
    libxml2 ImageMagick python3-pip xorg-x11-server-Xvfb \
    qt6-qtdeclarative-devel appstream 2>&1 | tail -3 || true
pip install --quiet --root-user-action=ignore check-jsonschema reuse 2>&1 | tail -2 || true

echo "== Bildschirmsperre und Energiesparen abschalten =="
# In einer Test-VM sind beide schaedlich: Nach ein paar Minuten Leerlauf
# liefert 'virsh screenshot' nur noch "Display output is not active" oder
# den Sperrbildschirm - ein automatisierter Testlauf sammelt dann schwarze
# Bilder ein und meldet trotzdem Erfolg.
sudo -u tester bash <<'USERCFG'
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
for p in AC Battery LowBattery; do
    kwriteconfig6 --file powermanagementprofilesrc --group "$p" \
        --group DPMSControl --key idleTime 0
    kwriteconfig6 --file powermanagementprofilesrc --group "$p" \
        --group DimDisplay --key idleTime 0
    kwriteconfig6 --file powermanagementprofilesrc --group "$p" \
        --group SuspendSession --key idleTime 0
done
USERCFG

echo "== Referenz sichern =="
# Der unveraenderte Breeze-Stand. Danach laesst sich jederzeit pruefen,
# was ein Theme-Installer am System veraendert hat.
mkdir -p /var/lib/plasma-lab
for f in plasmarc kdeglobals kwinrc ksplashrc; do
    cp -a "/home/tester/.config/$f" "/var/lib/plasma-lab/ref-$f" 2>/dev/null || true
done
rpm -qa --qf '%{NAME}\n' | sort > /var/lib/plasma-lab/ref-packages.txt

echo "== Versionen =="
plasmashell --version 2>/dev/null || true
kwin_wayland --version 2>/dev/null || true
GUEST

echo
echo "== Gegenprobe: KDE-Werkzeuge im Gast =="
ssh $SSH_OPTS "$VM_USER@$IP" 'for t in plasma-apply-desktoptheme plasma-apply-lookandfeel \
    plasma-apply-colorscheme kpackagetool6 kwriteconfig6 kreadconfig6 plasmawindowed \
    kwin_wayland spectacle xmllint check-jsonschema reuse; do
        printf "%-28s %s\n" "$t" "$(command -v $t || echo FEHLT)"
    done'

echo
echo "Provisionierung fertig. Jetzt sichern mit:"
echo "  $VM_DIR/vmctl.sh snap create clean"
