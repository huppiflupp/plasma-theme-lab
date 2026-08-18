#!/usr/bin/env bash
# Legt die zweite Test-VM an: EndeavourOS (Arch-Familie).
#
#   ./build-vm-eos.sh          # legt an, bricht ab wenn sie existiert
#   ./build-vm-eos.sh --force  # loescht eine bestehende vorher
#
# Anders als build-vm.sh laeuft das hier NICHT unbeaufsichtigt.
#
# Fedora installiert per Kickstart aus dem Netz; EndeavourOS bringt
# Calamares mit, einen grafischen Assistenten ohne Antwortdatei. Die
# zwanzig Minuten Klickarbeit sind der Preis dafuer, dass diese Familie
# ueberhaupt im Labor vertreten ist.
#
# Nach dem Durchklicken macht ./eos-fertig.sh die Maschine fernsteuerbar.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/eos.env"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

[ -f "$VM_ISO" ] || { echo "FEHLER: $VM_ISO fehlt."; exit 1; }

if virsh -c "$LIBVIRT_URI" dominfo "$VM_NAME" &>/dev/null; then
    if ! $FORCE; then
        echo "FEHLER: VM '$VM_NAME' existiert bereits."
        echo "        Neu bauen mit: $0 --force"
        exit 1
    fi
    echo "Entferne bestehende VM '$VM_NAME' …"
    virsh -c "$LIBVIRT_URI" destroy "$VM_NAME" &>/dev/null || true
    virsh -c "$LIBVIRT_URI" undefine "$VM_NAME" --nvram --remove-all-storage &>/dev/null || true
fi

echo "Lege '$VM_NAME' an (Disk: $VM_DISK, ${VM_DISK_GB} GB) …"

# Dieselben Eckdaten wie bei der Fedora-VM: q35, UEFI, virtio, SPICE ohne
# Netzwerk-Port, Guest-Agent. Letzterer ist keine Bequemlichkeit -
# vmctl.sh holt die IP darueber.
#
# Ein Unterschied ist noetig: Secure Boot aus.
#
# "--boot uefi" waehlt auf diesem Rechner die Firmware mit hinterlegten
# Schluesseln, und daran scheitert der Start vom EndeavourOS-Medium:
#
#   failed to load Boot0002 "UEFI QEMU DVD-ROM" ...
#   Access Denied -- rejected probably by Secure Boot
#   No bootable option or device was found.
#
# Fedora bootet dort, weil sein Startpfad signiert ist; ein
# Arch-Abkoemmling ist es nicht. Fuer eine Wegwerf-Testmaschine ist das
# Abschalten die richtige Antwort - Secure Boot ist hier nichts, was
# geprueft werden soll.
#
# Zweiter Unterschied: qxl statt virtio als Grafik.
#
# Mit virtio lief das Live-System einwandfrei - Xorg und die
# Willkommens-App liefen, der Guest-Agent antwortete -, aber
# "virsh screenshot" lieferte ein schwarzes Bild. Genau darauf beruht
# hier jeder Theme-Test: Bootmenue, Startbildschirm, Vorschaubilder.
# QXL legt einen klassischen Framebuffer vor, den der Hypervisor
# mitlesen kann.
virt-install \
    --connect "$LIBVIRT_URI" \
    --name "$VM_NAME" \
    --memory "$VM_RAM_MB" \
    --vcpus "$VM_VCPUS" \
    --cpu host-model \
    --machine q35 \
    --boot uefi,firmware.feature0.name=secure-boot,firmware.feature0.enabled=no \
    --disk "path=$VM_DISK,size=$VM_DISK_GB,format=qcow2,bus=virtio,cache=none,discard=unmap" \
    --cdrom "$VM_ISO" \
    --network "network=$VM_NETWORK,model=virtio" \
    --graphics spice,listen=none \
    --video qxl \
    --channel spicevmc \
    --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
    --rng /dev/urandom \
    --osinfo "$VM_OSINFO" \
    --noautoconsole

cat <<EOF

Die VM laeuft und bootet vom ISO. Jetzt der Installer:

    LAB_ENV=eos.env ./vmctl.sh viewer

Im Assistenten wichtig - danach richtet sich der Rest des Labors:

  * Bootloader:   GRUB   (nicht systemd-boot - die Bootskripte sollen
                          hier ja gerade auf der GRUB-Seite geprueft
                          werden)
  * Desktop:      KDE Plasma
  * Benutzer:     tester   mit Passwort   tester
                  (dieselben Werte wie in der Fedora-VM; die Maschine
                  ist ein Wegwerf-Ziel ohne Netzzugang von aussen)
  * Partition:    ganze Platte, Vorgaben uebernehmen

Danach einmal neu starten und weiter mit:

    ./eos-fertig.sh

EOF
