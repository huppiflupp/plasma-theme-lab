#!/usr/bin/env bash
# Makes the freshly installed EndeavourOS VM remote-controllable.
#
#   ./eos-finish.sh
#
# After Calamares the machine lacks three things that vmctl.sh needs:
# a running sshd, our key in it, and the guest agent (through
# which vmctl.sh gets the IP). Plus the marker file that wait_ssh
# waits for.
#
# The first step cannot be done from the host - without
# sshd you cannot get in. So on its first run this script prints
# a command that you run once in the VM; it then does everything
# else by itself.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/eos.env"

[ -f "$VM_DIR/id_lab.pub" ] || { echo "ERROR: id_lab.pub is missing."; exit 1; }
PUBKEY="$(cat "$VM_DIR/id_lab.pub")"

get_ip() {
    virsh -c "$LIBVIRT_URI" domifaddr "$VM_NAME" --source agent 2>/dev/null \
        | awk '$3=="ipv4" && $4!~/^127\./ {sub(/\/.*/,"",$4); print $4; exit}' \
    || true
    virsh -c "$LIBVIRT_URI" domifaddr "$VM_NAME" --source lease 2>/dev/null \
        | awk '$3=="ipv4" {sub(/\/.*/,"",$4); print $4; exit}' || true
}

IP="$(get_ip | head -1)"

if [ -z "$IP" ] || ! ssh $SSH_OPTS "$VM_USER@$IP" true 2>/dev/null; then
    cat <<EOF

The VM is not reachable yet. Log in to it, open a
terminal and run this line (in the viewer it can be pasted with
Ctrl+Shift+V):

sudo pacman -S --noconfirm --needed openssh qemu-guest-agent && sudo systemctl enable --now sshd qemu-guest-agent && install -d -m700 ~/.ssh && echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sudo touch /etc/plasma-lab-ready && echo 'tester ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/90-tester >/dev/null && sudo chmod 440 /etc/sudoers.d/90-tester && echo DONE

Then run this script once more:

    ./eos-finish.sh

EOF
    exit 1
fi

echo "Reachable at $IP."

# From here on everything goes over SSH. The guest agent is the only way
# vmctl.sh finds the IP later - without it only the
# DHCP lease would remain, and that is often stale after a snapshot revert.
#
# "ssh -t" is mandatory, not a convenience: without a TTY sudo aborts with
#
#   sudo: a terminal is required to read the password
#
# - and therein lies a chicken-and-egg problem that this script tripped over
# the first time: it sets up passwordless sudo and
# would already need it to do so. With -t sudo asks once, after that
# the rule is in place. Anyone who used the first-run command above is not
# asked at all - it creates the rule right away.
if ! ssh $SSH_OPTS "$VM_USER@$IP" 'sudo -n true' 2>/dev/null; then
    echo "Now enter the password of $VM_USER once (as set in the VM):"
fi
ssh -t $SSH_OPTS "$VM_USER@$IP" '
    set -e
    command -v qemu-ga >/dev/null || sudo pacman -S --noconfirm --needed qemu-guest-agent
    sudo systemctl enable --now qemu-guest-agent sshd
    sudo touch /etc/plasma-lab-ready
    # Without passwordless sudo every test script hangs at the first
    # sudo prompt. The tester has the same freedom in the Fedora VM.
    echo "tester ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/90-tester >/dev/null
    sudo chmod 440 /etc/sudoers.d/90-tester

    # Autologin. Without a logged-in session there is no Plasma bus, and
    # then plasma-apply-lookandfeel, -desktoptheme and
    # -colorscheme abort with SIGABRT ("core dumped"). That is exactly what
    # happened in this VM at first - apply.sh did set the values itself via
    # kwriteconfig6, but the background and panel stayed unchanged.
    #
    # Plasma 6.7 brings its own login manager
    # (plasma-login-manager, no longer SDDM); the configuration lives
    # in /etc/plasmalogin.conf and follows the structure of sddm.conf.
    printf "[Autologin]\nUser=tester\nSession=plasma\nRelogin=true\n" \
        | sudo tee /etc/plasmalogin.conf >/dev/null
    echo "  Guest agent, sshd, marker, sudo and autologin set up"
'

echo ""
echo "Quick function test:"
LAB_ENV=eos.env "$VM_DIR/vmctl.sh" ssh 'echo "  Distribution: $(. /etc/os-release; echo $PRETTY_NAME)"
echo "  Plasma:       $(plasmashell --version 2>/dev/null || echo "(not installed)")"
echo "  Bootloader:   $(test -d /boot/grub && echo "GRUB (/boot/grub)" || echo "NOT GRUB - see below")"
echo "  initramfs:    $(command -v dracut >/dev/null && echo dracut || (command -v mkinitcpio >/dev/null && echo mkinitcpio || echo "?"))"
echo "  sudo free:    $(sudo -n true 2>/dev/null && echo yes || echo NO)"'

cat <<EOF

If the bootloader above is not GRUB, the machine is useless for its
actual purpose - then install again and choose GRUB in the
wizard.

Otherwise record the initial state now:

    LAB_ENV=eos.env ./vmctl.sh snap create clean

EOF
