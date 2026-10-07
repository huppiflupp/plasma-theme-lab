#!/usr/bin/env bash
# Baut die Ubuntu-Test-VM (Ubuntu 26.04 LTS + KDE Plasma).
#
#   ./build-vm-ubuntu.sh          # baut, bricht ab wenn die VM schon existiert
#   ./build-vm-ubuntu.sh --force  # loescht eine bestehende VM vorher
#
# Unbeaufsichtigt: Grundlage ist das offizielle Cloud-Image, den Rest
# (kubuntu-desktop, Benutzer, Autologin, GRUB mit Splash) erledigt
# cloud-init aus ubuntu-lab.user-data. Am Ende startet die VM von selbst
# neu und meldet sich in Plasma an.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/ubuntu.env"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

if virsh -c "$LIBVIRT_URI" dominfo "$VM_NAME" &>/dev/null; then
    if ! $FORCE; then
        echo "FEHLER: VM '$VM_NAME' existiert bereits."
        echo "        Neu bauen mit: $0 --force"
        exit 1
    fi
    echo "[1/4] Entferne bestehende VM '$VM_NAME'..."
    virsh -c "$LIBVIRT_URI" destroy "$VM_NAME" &>/dev/null || true
    virsh -c "$LIBVIRT_URI" undefine "$VM_NAME" --nvram --remove-all-storage &>/dev/null || true
else
    echo "[1/4] Keine bestehende VM - baue neu."
fi

# --- Cloud-Image holen und pruefen -------------------------------------------
echo "[2/4] Cloud-Image..."
if [ ! -f "$UBUNTU_IMG.ok" ]; then
    curl -L -C - --fail --progress-bar -o "$UBUNTU_IMG" "$UBUNTU_IMG_URL"
    want=$(curl -sL --fail "$UBUNTU_SUMS_URL" \
           | awk -v f="*$(basename "$UBUNTU_IMG")" '$2==f {print $1}')
    have=$(sha256sum "$UBUNTU_IMG" | cut -d' ' -f1)
    [ -n "$want" ] && [ "$want" = "$have" ] \
        || { echo "FEHLER: Pruefsumme passt nicht ($have)."; exit 1; }
    echo "$have" > "$UBUNTU_IMG.ok"
fi

# Eigenstaendige Kopie statt Overlay auf das Image: eine Backing-Chain
# wuerde jeden Snapshot an die Datei in iso/ binden.
[ -e "$VM_DISK" ] && { echo "FEHLER: $VM_DISK existiert schon."; exit 1; }
qemu-img convert -O qcow2 "$UBUNTU_IMG" "$VM_DISK"
qemu-img resize "$VM_DISK" "${VM_DISK_GB}G" >/dev/null

# --- cloud-init mit dem echten Public-Key fuellen -----------------------------
echo "[3/4] Bereite cloud-init vor..."
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"
UD_RENDERED="$VM_DIR/.ubuntu-lab.rendered.user-data"
sed "s|SSH_PUBKEY_PLACEHOLDER|$PUBKEY|" "$VM_DIR/ubuntu-lab.user-data" > "$UD_RENDERED"
grep -q SSH_PUBKEY_PLACEHOLDER "$UD_RENDERED" && { echo "FEHLER: Platzhalter nicht ersetzt."; exit 1; }

# --- VM anlegen ---------------------------------------------------------------
# Eckdaten wie bei der Fedora-VM. Secure Boot darf an bleiben: Ubuntus
# Startpfad ist signiert (anders als bei EndeavourOS).
echo "[4/4] Lege '$VM_NAME' an, cloud-init installiert Plasma (20-30 min)..."
virt-install \
    --connect "$LIBVIRT_URI" \
    --name "$VM_NAME" \
    --memory "$VM_RAM_MB" \
    --vcpus "$VM_VCPUS" \
    --cpu host-model \
    --machine q35 \
    --boot uefi \
    --import \
    --disk "path=$VM_DISK,format=qcow2,bus=virtio,cache=none,discard=unmap" \
    --network "network=$VM_NETWORK,model=virtio" \
    --graphics spice,listen=none \
    --video virtio \
    --channel spicevmc \
    --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
    --rng /dev/urandom \
    --osinfo "$VM_OSINFO" \
    --cloud-init "user-data=$UD_RENDERED" \
    --noautoconsole

cat <<EOF

Die VM laeuft, cloud-init arbeitet. Fortschritt:

    LAB_ENV=ubuntu.env ./vmctl.sh shot
    LAB_ENV=ubuntu.env ./vmctl.sh ssh 'tail -f /var/log/cloud-init-output.log'

Am Ende faehrt die VM HERUNTER statt neu zu starten: virt-install legt
den ersten Lauf mit on_reboot=destroy an, damit das cloud-init-ISO
danach entfernt werden kann. Ist sie aus, einfach starten (wartet bis
40 min, falls cloud-init noch arbeitet):

    LAB_ENV=ubuntu.env ./vmctl.sh start 2400

Fehlt danach Plasma (cloud-init bricht bei Netzproblemen die
Paketinstallation ab, ohne den Bau scheitern zu lassen):

    grep -i fail /var/log/cloud-init-output.log    # in der VM
    ./ubuntu-provision.sh

Kommt die VM gar nicht ins Netz: Docker auf dem Host setzt die
FORWARD-Policy auf DROP. Siehe .cockpit/notes.md.

Danach den Ausgangszustand festhalten:

    LAB_ENV=ubuntu.env ./vmctl.sh snap create clean
EOF
