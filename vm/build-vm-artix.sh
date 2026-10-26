#!/usr/bin/env bash
# Builds the Artix test VM (Artix Linux, OpenRC, Plasma 6) unattended.
#
#   ./build-vm-artix.sh          # builds, aborts if the VM already exists
#   ./build-vm-artix.sh --force  # deletes an existing VM first
#
# How, since Artix has no answer file and the VMs have no internet:
#
#  1. boot the official base ISO (checksum checked) in a new VM;
#  2. type one line into the live system's console through the hypervisor
#     (HMP sendkey): log in as root, put the lab key in, start sshd;
#  3. over SSH, with a reverse tunnel to connect-proxy.py on the host
#     (the only way out: Docker's FORWARD DROP), run artix-install.sh:
#     every package from Artix's archive of ARTIX_ARCHIVE_DATE, so a
#     rebuild gives the same versions;
#  4. boot the installed system without the ISO, wait for Plasma, take the
#     snapshot 'clean'.
#
# About 15 minutes, most of it downloading ~1.5 GB of packages.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/artix.env"
V() { virsh -c "$LIBVIRT_URI" "$@"; }

FORCE=false
[ "${1:-}" = "--force" ] && FORCE=true

if V dominfo "$VM_NAME" &>/dev/null; then
    $FORCE || { echo "ERROR: VM '$VM_NAME' already exists. Rebuild with: $0 --force"; exit 1; }
    echo "[1/6] Removing existing VM '$VM_NAME'..."
    V destroy "$VM_NAME" &>/dev/null || true
    for s in $(V snapshot-list "$VM_NAME" --name 2>/dev/null); do V snapshot-delete "$VM_NAME" "$s" >/dev/null; done
    V undefine "$VM_NAME" --nvram --remove-all-storage &>/dev/null || true
else
    echo "[1/6] No existing VM - building from scratch."
fi

# --- the ISO, checked ----------------------------------------------------------
echo "[2/6] ISO..."
mkdir -p "$(dirname "$ARTIX_ISO")"
if [ ! -f "$ARTIX_ISO.ok" ]; then
    curl -L -C - --fail --progress-bar -o "$ARTIX_ISO" "$ARTIX_ISO_URL"
    want=$(curl -sL --fail "$ARTIX_SUMS_URL" | awk -v f="$(basename "$ARTIX_ISO")" '$2==f {print $1}')
    have=$(sha256sum "$ARTIX_ISO" | cut -d' ' -f1)
    [ -n "$want" ] && [ "$want" = "$have" ] || { echo "ERROR: checksum does not match ($have)."; exit 1; }
    echo "$have" > "$ARTIX_ISO.ok"
fi

# --- the tester's password: generated, kept out of git ------------------------
[ -f "$VM_PASSWORD_FILE" ] || { (umask 077; openssl rand -base64 12 > "$VM_PASSWORD_FILE"); }
PASSWORD_HASH=$(openssl passwd -6 -stdin < "$VM_PASSWORD_FILE")
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"

# --- the VM ---------------------------------------------------------------------
# As the other lab VMs: q35, UEFI, virtio, SPICE without a network port,
# guest agent (vmctl.sh gets the IP through it). Secure Boot off: Artix's
# boot path is not signed (as EndeavourOS, see build-vm-eos.sh).
echo "[3/6] Creating '$VM_NAME' (disk: $VM_DISK, ${VM_DISK_GB} GB)..."
virt-install \
    --connect "$LIBVIRT_URI" \
    --name "$VM_NAME" \
    --memory "$VM_RAM_MB" \
    --vcpus "$VM_VCPUS" \
    --cpu host-model \
    --machine q35 \
    --boot uefi,firmware.feature0.name=secure-boot,firmware.feature0.enabled=no \
    --disk "path=$VM_DISK,size=$VM_DISK_GB,format=qcow2,bus=virtio,cache=none,discard=unmap" \
    --cdrom "$ARTIX_ISO" \
    --network "network=$VM_NETWORK,model=virtio" \
    --graphics spice,listen=none \
    --video virtio \
    --channel spicevmc \
    --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
    --rng /dev/urandom \
    --osinfo "$VM_OSINFO" \
    --noautoconsole >/dev/null

# --- into the live system ------------------------------------------------------
# HMP sendkey speaks US key names; the live console has the US layout.
key() { V qemu-monitor-command "$VM_NAME" --hmp "sendkey $1" >/dev/null; sleep 0.04; }
type_text() {
    local s="$1" i c k
    for ((i = 0; i < ${#s}; i++)); do
        c="${s:i:1}"
        case "$c" in
            [a-z0-9]) k="$c" ;;
            [A-Z]) k="shift-${c,,}" ;;
            ' ') k=spc ;; '-') k=minus ;; '=') k=equal ;; '/') k=slash ;; '.') k=dot ;;
            ',') k=comma ;; ';') k=semicolon ;; "'") k=apostrophe ;; '>') k=shift-dot ;;
            '+') k=shift-equal ;; '_') k=shift-minus ;; ':') k=shift-semicolon ;; '@') k=shift-2 ;;
            '&') k=shift-7 ;; '|') k=shift-backslash ;; '"') k=shift-apostrophe ;;
            *) echo "ERROR: cannot type '$c'" >&2; return 1 ;;
        esac
        key "$k"
    done
}
lease_ip() {
    V domifaddr "$VM_NAME" --source lease 2>/dev/null | awk '$3=="ipv4" {sub(/\/.*/,"",$4); print $4; exit}'
}

echo "[4/6] Live system: waiting for it to boot..."
# The ISO's GRUB menu has no timeout and the cursor on "keytable=us"; two
# down from there is "From CD/DVD/ISO". The live system then asks for a
# login on tty1 and takes an address by DHCP.
sleep 25
key down; key down; key ret
for _ in $(seq 90); do [ -n "$(lease_ip)" ] && break; sleep 5; done
[ -n "$(lease_ip)" ] || { echo "ERROR: the live system took no address."; exit 1; }
sleep 15
# Keys typed while the console is still settling can get lost (seen on
# the first run): up to three tries, each checked by an SSH login.
LIVE=$(lease_ip)
for try in 1 2 3; do
    key ret; sleep 2
    type_text "root"; key ret; sleep 2
    type_text "artix"; key ret; sleep 4
    type_text "mkdir -p .ssh; echo '$PUBKEY' > .ssh/authorized_keys; rc-service sshd start"; key ret
    for _ in $(seq 10); do ssh $SSH_OPTS "root@$LIVE" true 2>/dev/null && break 2; sleep 3; done
    echo "  try $try: no SSH yet, typing again"
done
ssh $SSH_OPTS "root@$LIVE" true || { echo "ERROR: no SSH into the live system ($LIVE)."; exit 1; }

echo "[5/6] Installing (archive of $ARTIX_ARCHIVE_DATE, through the host's proxy)..."
python3 "$VM_DIR/connect-proxy.py" --port 3129 > "$VM_DIR/artix-proxy.log" 2>&1 &
PROXY=$!
trap 'kill $PROXY 2>/dev/null || true' EXIT
sleep 1
scp $SSH_OPTS -q "$VM_DIR/artix-install.sh" "root@$LIVE:/root/"
ssh $SSH_OPTS -R 3129:127.0.0.1:3129 "root@$LIVE" \
    "ARCHIVE_DATE='$ARTIX_ARCHIVE_DATE' PUBKEY='$PUBKEY' PASSWORD_HASH='$PASSWORD_HASH' \
     https_proxy=http://127.0.0.1:3129 http_proxy=http://127.0.0.1:3129 bash /root/artix-install.sh" \
    2>&1 | tee "$VM_DIR/artix-build.log"
grep -q "== Installed ==" "$VM_DIR/artix-build.log" || { echo "ERROR: installation failed, see artix-build.log"; exit 1; }
kill $PROXY 2>/dev/null || true

# --- first boot of the installed system ----------------------------------------
echo "[6/6] First boot..."
V destroy "$VM_NAME" >/dev/null
# The ISO out of the drive, the disk first.
CDROM=$(V domblklist "$VM_NAME" --details | awk '$2=="cdrom" {print $3; exit}')
# virt-install may have emptied the drive itself already.
[ -n "$CDROM" ] && { V change-media "$VM_NAME" "$CDROM" --eject --config &>/dev/null || true; }
V start "$VM_NAME" >/dev/null
LAB_ENV=artix.env "$VM_DIR/vmctl.sh" start 600
sleep 20   # Plasma after the autologin
LAB_ENV=artix.env "$VM_DIR/vmctl.sh" shot "$VM_DIR/../tests/screenshots/artix-first-boot.png"
LAB_ENV=artix.env "$VM_DIR/vmctl.sh" snap create clean

cat <<EOF

Done. The VM '$VM_NAME' is installed, snapshot 'clean' exists.
    LAB_ENV=artix.env ./vmctl.sh start
    LAB_ENV=artix.env ./vmctl.sh ssh
The tester's password is in $(basename "$VM_PASSWORD_FILE") (git-ignored).
EOF
