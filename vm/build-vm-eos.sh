#!/usr/bin/env bash
# Creates the second test VM: EndeavourOS (Arch family).
#
#   ./build-vm-eos.sh          # creates it, aborts if it exists
#   ./build-vm-eos.sh --force  # deletes an existing one first
#
# Unlike build-vm.sh, this does NOT run unattended.
#
# Fedora installs from the network via kickstart; EndeavourOS ships
# Calamares, a graphical wizard without an answer file. The
# twenty minutes of clicking are the price for having this family
# represented in the lab at all.
#
# After clicking through, ./eos-finish.sh makes the machine remote-controllable.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/eos.env"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

[ -f "$VM_ISO" ] || { echo "ERROR: $VM_ISO is missing."; exit 1; }

if virsh -c "$LIBVIRT_URI" dominfo "$VM_NAME" &>/dev/null; then
    if ! $FORCE; then
        echo "ERROR: VM '$VM_NAME' already exists."
        echo "       Rebuild with: $0 --force"
        exit 1
    fi
    echo "Removing existing VM '$VM_NAME' …"
    virsh -c "$LIBVIRT_URI" destroy "$VM_NAME" &>/dev/null || true
    virsh -c "$LIBVIRT_URI" undefine "$VM_NAME" --nvram --remove-all-storage &>/dev/null || true
fi

echo "Creating '$VM_NAME' (disk: $VM_DISK, ${VM_DISK_GB} GB) …"

# The same key parameters as for the Fedora VM: q35, UEFI, virtio, SPICE without
# a network port, guest agent. The latter is not a convenience -
# vmctl.sh gets the IP through it.
#
# One difference is necessary: Secure Boot off.
#
# "--boot uefi" on this machine picks the firmware with enrolled
# keys, and booting from the EndeavourOS medium fails on that:
#
#   failed to load Boot0002 "UEFI QEMU DVD-ROM" ...
#   Access Denied -- rejected probably by Secure Boot
#   No bootable option or device was found.
#
# Fedora boots there because its boot path is signed; an
# Arch derivative's is not. For a disposable test machine, switching it
# off is the right answer - Secure Boot is not something to be
# tested here.
#
# Second difference: qxl instead of virtio for graphics.
#
# With virtio the live system ran flawlessly - Xorg and the
# welcome app ran, the guest agent answered - but
# "virsh screenshot" returned a black image. Every theme test here
# relies on exactly that: boot menu, splash screen, preview images.
# QXL provides a classic framebuffer that the hypervisor
# can read along.
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

The VM is running and booting from the ISO. Now the installer:

    LAB_ENV=eos.env ./vmctl.sh viewer

Important in the wizard - the rest of the lab depends on it:

  * Bootloader:   GRUB   (not systemd-boot - the whole point is to
                          test the boot scripts on the GRUB side
                          here)
  * Desktop:      KDE Plasma
  * User:         tester   with password   tester
                  (the same values as in the Fedora VM; the machine
                  is a disposable target without network access from outside)
  * Partition:    whole disk, accept the defaults

Then reboot once and continue with:

    ./eos-finish.sh

EOF
