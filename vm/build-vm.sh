#!/usr/bin/env bash
# Builds the Plasma theme test VM from scratch.
#
# Network installation of Fedora 44 KDE via kickstart - no ISO is
# downloaded, Anaconda fetches the packages directly from the mirror.
#
#   ./build-vm.sh          # builds, aborts if the VM already exists
#   ./build-vm.sh --force  # deletes an existing VM first

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/lab.env"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

# --- handle an existing VM --------------------------------------------------
if virsh -c "$LIBVIRT_URI" dominfo "$VM_NAME" &>/dev/null; then
    if ! $FORCE; then
        echo "ERROR: VM '$VM_NAME' already exists."
        echo "       Rebuild with: $0 --force"
        exit 1
    fi
    echo "[1/4] Removing existing VM '$VM_NAME'..."
    virsh -c "$LIBVIRT_URI" destroy "$VM_NAME" &>/dev/null || true
    virsh -c "$LIBVIRT_URI" undefine "$VM_NAME" --nvram --remove-all-storage &>/dev/null || true
else
    echo "[1/4] No existing VM - building from scratch."
fi

# --- fill the kickstart with the real public key ----------------------------
echo "[2/4] Preparing kickstart..."
[ -f "$VM_DIR/id_lab.pub" ] || { echo "ERROR: $VM_DIR/id_lab.pub is missing."; exit 1; }
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"
KS_RENDERED="$VM_DIR/.plasma-lab.rendered.ks"
sed "s|SSH_PUBKEY_PLACEHOLDER|$PUBKEY|" "$VM_DIR/plasma-lab.ks" > "$KS_RENDERED"
grep -q SSH_PUBKEY_PLACEHOLDER "$KS_RENDERED" && { echo "ERROR: placeholder not replaced."; exit 1; }

# --- start the installation -------------------------------------------------
echo "[3/4] Starting unattended installation (takes 20-40 min)..."
echo "      Watch progress:      virt-viewer --attach -c $LIBVIRT_URI $VM_NAME"
echo "      or on the console:   virsh -c $LIBVIRT_URI console $VM_NAME"

echo "      View the screen:     ./vmctl.sh shot /tmp/installer.png"
echo "      Into the installer:  ssh root@<ip>   (password: lab)"

# Deliberately NO '--serial file': libvirt creates the target file as root:root
# 0600, so it is not readable without sudo - and on the next run
# even creating it fails because of that. Diagnosis goes through
# the graphical screen (console=tty0) and inst.sshd instead.
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

# On the choice of console=tty0: Anaconda draws its text interface on
# the console given last. With console=ttyS0 it ends up on the
# serial port - but libvirt creates its log file as
# root:root 0600, and you cannot get at the pty without root either.
# A hanging installation would then be a black box. On tty0 it is
# visible at any time via 'vmctl.sh shot'.
#
# inst.sshd + inst.rootpw additionally open SSH access INTO the
# running installer (root@<ip>, password 'lab'), to read /tmp/anaconda.log
# and /tmp/packaging.log directly. Only active during the installation
# - the installed system uses the key from the kickstart.

echo "[4/4] Installation finished, VM is rebooting."
echo
echo "Next step:  $VM_DIR/wait-ready.sh && $VM_DIR/snapshot.sh create clean"
