#!/usr/bin/env bash
# Builds the Ubuntu test VM (Ubuntu 26.04 LTS + KDE Plasma).
#
#   ./build-vm-ubuntu.sh          # builds, aborts if the VM already exists
#   ./build-vm-ubuntu.sh --force  # deletes an existing VM first
#
# Unattended: the basis is the official cloud image, the rest
# (kubuntu-desktop, user, autologin, GRUB with splash) is done by
# cloud-init from ubuntu-lab.user-data. At the end the VM reboots by itself
# and logs into Plasma.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/ubuntu.env"

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

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

# --- fetch and verify the cloud image ----------------------------------------
echo "[2/4] Cloud image..."
if [ ! -f "$UBUNTU_IMG.ok" ]; then
    curl -L -C - --fail --progress-bar -o "$UBUNTU_IMG" "$UBUNTU_IMG_URL"
    want=$(curl -sL --fail "$UBUNTU_SUMS_URL" \
           | awk -v f="*$(basename "$UBUNTU_IMG")" '$2==f {print $1}')
    have=$(sha256sum "$UBUNTU_IMG" | cut -d' ' -f1)
    [ -n "$want" ] && [ "$want" = "$have" ] \
        || { echo "ERROR: checksum does not match ($have)."; exit 1; }
    echo "$have" > "$UBUNTU_IMG.ok"
fi

# A standalone copy instead of an overlay on the image: a backing chain
# would tie every snapshot to the file in iso/.
[ -e "$VM_DISK" ] && { echo "ERROR: $VM_DISK already exists."; exit 1; }
qemu-img convert -O qcow2 "$UBUNTU_IMG" "$VM_DISK"
qemu-img resize "$VM_DISK" "${VM_DISK_GB}G" >/dev/null

# --- fill cloud-init with the real public key -------------------------------
echo "[3/4] Preparing cloud-init..."
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"
UD_RENDERED="$VM_DIR/.ubuntu-lab.rendered.user-data"
sed "s|SSH_PUBKEY_PLACEHOLDER|$PUBKEY|" "$VM_DIR/ubuntu-lab.user-data" > "$UD_RENDERED"
grep -q SSH_PUBKEY_PLACEHOLDER "$UD_RENDERED" && { echo "ERROR: placeholder not replaced."; exit 1; }

# --- create the VM ----------------------------------------------------------
# Key parameters as for the Fedora VM. Secure Boot may stay on: Ubuntu's
# boot path is signed (unlike EndeavourOS).
echo "[4/4] Creating '$VM_NAME', cloud-init installs Plasma (20-30 min)..."
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

The VM is running, cloud-init is working. Progress:

    LAB_ENV=ubuntu.env ./vmctl.sh shot
    LAB_ENV=ubuntu.env ./vmctl.sh ssh 'tail -f /var/log/cloud-init-output.log'

At the end the VM SHUTS DOWN instead of rebooting: virt-install sets up
the first run with on_reboot=destroy so that the cloud-init ISO
can be removed afterwards. Once it is off, just start it (waits up to
40 min in case cloud-init is still working):

    LAB_ENV=ubuntu.env ./vmctl.sh start 2400

If Plasma is missing afterwards (on network problems cloud-init aborts the
package installation without failing the build):

    grep -i fail /var/log/cloud-init-output.log    # in the VM
    ./ubuntu-provision.sh

If the VM cannot reach the network at all: Docker on the host sets the
FORWARD policy to DROP. See .cockpit/notes.md.

Then record the initial state:

    LAB_ENV=ubuntu.env ./vmctl.sh snap create clean
EOF
