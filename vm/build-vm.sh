#!/usr/bin/env bash
# Baut die Plasma-Theme-Test-VM von Grund auf neu.
#
# Netzinstallation von Fedora 44 KDE per Kickstart - es wird kein ISO
# heruntergeladen, Anaconda holt sich die Pakete direkt vom Mirror.
#
#   ./build-vm.sh          # baut, bricht ab wenn die VM schon existiert
#   ./build-vm.sh --force  # loescht eine bestehende VM vorher

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/lab.env"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

# --- bestehende VM behandeln -------------------------------------------------
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

# --- Kickstart mit dem echten Public-Key fuellen ------------------------------
echo "[2/4] Bereite Kickstart vor..."
[ -f "$VM_DIR/id_lab.pub" ] || { echo "FEHLER: $VM_DIR/id_lab.pub fehlt."; exit 1; }
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"
KS_RENDERED="$VM_DIR/.plasma-lab.rendered.ks"
sed "s|SSH_PUBKEY_PLACEHOLDER|$PUBKEY|" "$VM_DIR/plasma-lab.ks" > "$KS_RENDERED"
grep -q SSH_PUBKEY_PLACEHOLDER "$KS_RENDERED" && { echo "FEHLER: Platzhalter nicht ersetzt."; exit 1; }

# --- Installation starten ----------------------------------------------------
echo "[3/4] Starte unbeaufsichtigte Installation (dauert 20-40 min)..."
echo "      Fortschritt ansehen:  virt-viewer --attach -c $LIBVIRT_URI $VM_NAME"
echo "      oder auf der Konsole: virsh -c $LIBVIRT_URI console $VM_NAME"

echo "      Bildschirm ansehen:  ./vmctl.sh shot /tmp/installer.png"
echo "      In den Installer:    ssh root@<ip>   (Passwort: lab)"

# Bewusst KEIN '--serial file': libvirt legt die Zieldatei als root:root
# 0600 an, sie ist also ohne sudo nicht lesbar - und beim naechsten Lauf
# scheitert schon das Anlegen daran. Die Diagnose laeuft stattdessen ueber
# den Grafikbildschirm (console=tty0) und ueber inst.sshd.
virt-install \
    --connect "$LIBVIRT_URI" \
    --name "$VM_NAME" \
    --memory "$VM_RAM_MB" \
    --vcpus "$VM_VCPUS" \
    --cpu host-model \
    --machine q35 \
    --boot uefi \
    --disk "path=$VM_DISK,size=$VM_DISK_GB,format=qcow2,bus=virtio,cache=none,discard=unmap" \
    --network "network=$VM_NETWORK,model=virtio" \
    --graphics spice,listen=none \
    --video virtio \
    --channel spicevmc \
    --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
    --console pty,target_type=serial \
    --rng /dev/urandom \
    --osinfo "$VM_OSINFO" \
    --location "$INSTALL_URL" \
    --initrd-inject "$KS_RENDERED" \
    --extra-args "inst.ks=file:/$(basename "$KS_RENDERED") inst.text console=tty0 inst.sshd inst.rootpw=lab" \
    --noautoconsole \
    --wait -1

# Zur Wahl von console=tty0: Anaconda zeichnet seine Textoberflaeche auf
# die zuletzt angegebene Konsole. Mit console=ttyS0 landet sie auf der
# seriellen Schnittstelle - deren Log-Datei legt libvirt aber als
# root:root 0600 an, und an das pty kommt man ohne Root ebenfalls nicht.
# Eine haengende Installation waere damit eine Blackbox. Auf tty0 ist sie
# per 'vmctl.sh shot' jederzeit sichtbar.
#
# inst.sshd + inst.rootpw oeffnen zusaetzlich einen SSH-Zugang IN den
# laufenden Installer (root@<ip>, Passwort 'lab'), um /tmp/anaconda.log
# und /tmp/packaging.log direkt zu lesen. Nur waehrend der Installation
# aktiv - das installierte System nutzt den Key aus dem Kickstart.

echo "[4/4] Installation abgeschlossen, VM startet neu."
echo
echo "Naechster Schritt:  $VM_DIR/wait-ready.sh && $VM_DIR/snapshot.sh create clean"
