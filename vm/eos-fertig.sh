#!/usr/bin/env bash
# Macht die frisch installierte EndeavourOS-VM fernsteuerbar.
#
#   ./eos-fertig.sh
#
# Nach Calamares fehlen der Maschine drei Dinge, die vmctl.sh braucht:
# ein laufender sshd, unser Schluessel darin, und der Guest-Agent (ueber
# den vmctl.sh die IP holt). Dazu die Marker-Datei, auf die wait_ssh
# wartet.
#
# Der erste Schritt laesst sich nicht vom Host aus erledigen - ohne
# sshd kommt man nicht hinein. Deshalb gibt dieses Skript beim ersten
# Aufruf einen Befehl aus, den man einmal in der VM ausfuehrt; alles
# Weitere macht es dann selbst.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/eos.env"

[ -f "$VM_DIR/id_lab.pub" ] || { echo "FEHLER: id_lab.pub fehlt."; exit 1; }
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"

ip_holen() {
    virsh -c "$LIBVIRT_URI" domifaddr "$VM_NAME" --source agent 2>/dev/null \
        | awk '$3=="ipv4" && $4!~/^127\./ {sub(/\/.*/,"",$4); print $4; exit}' \
    || true
    virsh -c "$LIBVIRT_URI" domifaddr "$VM_NAME" --source lease 2>/dev/null \
        | awk '$3=="ipv4" {sub(/\/.*/,"",$4); print $4; exit}' || true
}

IP="$(ip_holen | head -1)"

if [ -z "$IP" ] || ! ssh $SSH_OPTS "$VM_USER@$IP" true 2>/dev/null; then
    cat <<EOF

Die VM ist noch nicht erreichbar. Melde dich in ihr an, oeffne ein
Terminal und fuehre diese Zeile aus (im Viewer laesst sie sich mit
Strg+Umschalt+V einfuegen):

sudo pacman -S --noconfirm --needed openssh qemu-guest-agent && sudo systemctl enable --now sshd qemu-guest-agent && install -d -m700 ~/.ssh && echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sudo touch /etc/plasma-lab-ready && echo FERTIG

Danach dieses Skript noch einmal starten:

    ./eos-fertig.sh

EOF
    exit 1
fi

echo "Erreichbar unter $IP."

# Ab hier geht alles ueber SSH. Der Guest-Agent ist der einzige Weg, auf
# dem vmctl.sh spaeter die IP findet - ohne ihn bliebe nur der
# DHCP-Lease, und der ist nach einem Snapshot-Revert gern veraltet.
ssh $SSH_OPTS "$VM_USER@$IP" '
    set -e
    command -v qemu-ga >/dev/null || sudo pacman -S --noconfirm --needed qemu-guest-agent
    sudo systemctl enable --now qemu-guest-agent sshd
    sudo touch /etc/plasma-lab-ready
    # Ohne Passwortfreiheit haengt jedes Testskript an der ersten
    # sudo-Abfrage. Dieselbe Freiheit hat der tester in der Fedora-VM.
    echo "tester ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/90-tester >/dev/null
    sudo chmod 440 /etc/sudoers.d/90-tester
    echo "  Guest-Agent, sshd, Marker und sudo eingerichtet"
'

echo ""
echo "Kurzer Funktionstest:"
LAB_ENV=eos.env "$VM_DIR/vmctl.sh" ssh 'echo "  Distribution: $(. /etc/os-release; echo $PRETTY_NAME)"
echo "  Plasma:       $(plasmashell --version 2>/dev/null || echo "(nicht installiert)")"
echo "  Bootloader:   $(test -d /boot/grub && echo "GRUB (/boot/grub)" || echo "NICHT GRUB - siehe unten")"
echo "  initramfs:    $(command -v mkinitcpio >/dev/null && echo mkinitcpio || echo "?")"'

cat <<EOF

Steht der Bootloader oben nicht auf GRUB, ist die Maschine fuer den
eigentlichen Zweck unbrauchbar - dann noch einmal installieren und im
Assistenten GRUB waehlen.

Sonst jetzt den Ausgangszustand festhalten:

    LAB_ENV=eos.env ./vmctl.sh snap create clean

EOF
