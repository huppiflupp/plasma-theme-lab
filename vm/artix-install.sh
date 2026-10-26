#!/bin/bash
# Installs Artix (OpenRC) with Plasma onto /dev/vda - runs as root in the
# Artix live system, started by build-vm-artix.sh over SSH:
#
#   ARCHIVE_DATE=2026/10/25 PUBKEY='ssh-ed25519 …' PASSWORD_HASH='$6$…' \
#   https_proxy=http://127.0.0.1:3128 bash artix-install.sh
#
# Every package comes from Artix's archive of that date (the same versions
# on every rebuild); the proxy is the host's, through the SSH tunnel.
# The result: UEFI + GRUB, ext4, German locale and keyboard (as the other
# lab VMs), user tester with the lab key and passwordless sudo, SDDM
# logging tester straight into a Plasma Wayland session, OpenRC services
# sshd, dbus, elogind, NetworkManager, qemu-guest-agent, sddm.
set -euo pipefail
: "${ARCHIVE_DATE:?}" "${PUBKEY:?}" "${PASSWORD_HASH:?}"
DISK=/dev/vda
MIRROR="Server = https://archive.artixlinux.org/repos/$ARCHIVE_DATE/\$repo/os/\$arch"

# The fixed package list. Plasma without the meta packages' extras: the
# desktop, what the theme scripts call (kwriteconfig6, plasma-apply-*,
# qdbus6, kquitapp6), Dolphin, Konsole, Kvantum, and the tools the lab
# scripts use in the guest (rsync, ImageMagick, xmllint).
PACKAGES=(
    base base-devel openrc elogind-openrc dbus-openrc linux linux-firmware mkinitcpio
    grub efibootmgr sudo nano rsync imagemagick libxml2 python zip unzip which
    openssh-openrc networkmanager-openrc qemu-guest-agent-openrc
    sddm sddm-openrc
    plasma-desktop plasma-workspace kwin xorg-xwayland plasma-nm plasma-pa powerdevil kscreen
    systemsettings kde-cli-tools kde-gtk-config xdg-desktop-portal-kde polkit-kde-agent
    breeze dolphin konsole kdialog kvantum qt6-svg gtk-update-icon-cache
    pipewire pipewire-pulse wireplumber mesa
    noto-fonts ttf-dejavu xdg-user-dirs
)

echo "== Package source: archive of $ARCHIVE_DATE =="
echo "$MIRROR" > /etc/pacman.d/mirrorlist
# The live system's keyring is older than the archive date.
pacman -Sy --noconfirm artix-keyring
pacman-key --populate artix

echo "== Disk =="
wipefs -af "$DISK"
sfdisk --quiet "$DISK" <<EOF
label: gpt
size=512MiB, type=uefi, name=ESP
type=linux, name=root
EOF
udevadm settle 2>/dev/null || sleep 2
mkfs.fat -F32 -n ESP "${DISK}1"
mkfs.ext4 -q -F -L artix "${DISK}2"
mount "${DISK}2" /mnt
mkdir -p /mnt/boot/efi
mount "${DISK}1" /mnt/boot/efi

echo "== basestrap =="
basestrap /mnt "${PACKAGES[@]}"
fstabgen -U /mnt >> /mnt/etc/fstab
cp /etc/pacman.d/mirrorlist /mnt/etc/pacman.d/mirrorlist

echo "== System =="
artix-chroot /mnt /bin/bash -s -- "$PUBKEY" "$PASSWORD_HASH" <<'CHROOT'
set -euo pipefail
PUBKEY=$1; PASSWORD_HASH=$2
export LANG=C.UTF-8   # the live system's "C" makes every Qt tool complain
ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime
hwclock --systohc || true
sed -i 's/^#\(de_DE.UTF-8 UTF-8\)/\1/; s/^#\(en_US.UTF-8 UTF-8\)/\1/' /etc/locale.gen
locale-gen >/dev/null
echo 'LANG=de_DE.UTF-8' > /etc/locale.conf
# Commands over SSH get no LANG here (neither SetEnv nor pam_env took);
# vmctl.sh ssh reads it from locale.conf.
echo 'keymap="de-latin1"' > /etc/conf.d/keymaps
mkdir -p /etc/X11/xorg.conf.d
printf 'Section "InputClass"\n  Identifier "keyboard"\n  MatchIsKeyboard "yes"\n  Option "XkbLayout" "de"\nEndSection\n' \
    > /etc/X11/xorg.conf.d/00-keyboard.conf
echo artix-lab > /etc/hostname
echo 'hostname="artix-lab"' > /etc/conf.d/hostname
printf '127.0.0.1 localhost\n::1 localhost\n127.0.1.1 artix-lab\n' > /etc/hosts

# The user, the key, sudo without a password (as in the other lab VMs).
useradd -m -G wheel,video,audio,input -s /bin/bash -p "$PASSWORD_HASH" tester
install -d -m700 -o tester -g tester /home/tester/.ssh
echo "$PUBKEY" > /home/tester/.ssh/authorized_keys
chown tester:tester /home/tester/.ssh/authorized_keys; chmod 600 /home/tester/.ssh/authorized_keys
echo 'tester ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/90-tester; chmod 440 /etc/sudoers.d/90-tester
usermod -p '!' root

# Services. The display manager: Artix's sddm-openrc ships /etc/init.d/sddm;
# older ones used the generic "displaymanager" service.
rc-update add elogind boot
for s in dbus NetworkManager sshd qemu-guest-agent; do rc-update add "$s" default; done
if [ -e /etc/init.d/sddm ]; then
    rc-update add sddm default
else
    sed -i 's/^DISPLAYMANAGER=.*/DISPLAYMANAGER="sddm"/' /etc/conf.d/displaymanager 2>/dev/null || \
        echo 'DISPLAYMANAGER="sddm"' > /etc/conf.d/displaymanager
    rc-update add displaymanager default
fi

# SDDM takes VT 1, where Artix runs a getty: whoever starts first wins, and
# when the getty does, the autologin loops ("Failed to take control of
# /dev/tty1", second boot of the first build). tty2-6 keep theirs.
rc-update del agetty.tty1 default 2>/dev/null || true

# No connectivity check: the lab VMs have no internet by design, and the
# "limited connection" notification would sit in every screenshot.
mkdir -p /etc/NetworkManager/conf.d
printf '[connectivity]\nenabled=false\n' > /etc/NetworkManager/conf.d/90-plasma-lab.conf

# Autologin into Plasma on Wayland, and again after logging out.
mkdir -p /etc/sddm.conf.d
printf '[Autologin]\nUser=tester\nSession=plasma\nRelogin=true\n\n[General]\nDisplayServer=wayland\n' \
    > /etc/sddm.conf.d/10-plasma-lab.conf

# No systemd, so no user bus at /run/user/1000/bus: SDDM starts the
# session under dbus-run-session, at an address of its own. The lab's
# scripts (vmctl.sh ssh) find it in this file. Nothing else is changed:
# the session is the one an OpenRC user has.
# install -d gives only the last directory the owner: every level named.
install -d -o tester -g tester /home/tester/.config /home/tester/.config/plasma-workspace \
    /home/tester/.config/plasma-workspace/env
cat > /home/tester/.config/plasma-workspace/env/plasma-lab-bus.sh <<'ENV'
# plasma-lab: tell the lab scripts where this session's D-Bus is.
[ -n "$DBUS_SESSION_BUS_ADDRESS" ] && [ -n "$XDG_RUNTIME_DIR" ] && \
    printf '%s\n' "$DBUS_SESSION_BUS_ADDRESS" > "$XDG_RUNTIME_DIR/bus-address"
ENV

# Quiet test machine: no screen lock, no dimming, no suspend, no welcome.
sudo -H -u tester bash <<'USERCFG'
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume false
kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 0
for p in AC Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key DimDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group Display --key TurnOffDisplayWhenIdle false
    kwriteconfig6 --file powerdevilrc --group "$p" --group SuspendAndShutdown --key AutoSuspendAction 0
done
kwriteconfig6 --file kxkbrc --group Layout --key LayoutList de
kwriteconfig6 --file kxkbrc --group Layout --key Use true
printf '[General]\nLastSeenVersion=99.99.99\n' > ~/.config/plasma-welcomerc
USERCFG
chown -R tester:tester /home/tester

# GRUB. --removable: the fallback path EFI/BOOT/BOOTX64.EFI, so the VM
# also boots after an NVRAM reset (snapshot reverts).
sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=3/' /etc/default/grub
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=artix --removable
grub-mkconfig -o /boot/grub/grub.cfg 2>&1 | tail -1

mkdir -p /var/lib/plasma-lab
pacman -Q > /var/lib/plasma-lab/ref-packages.txt
touch /etc/plasma-lab-ready
CHROOT

umount -R /mnt
echo "== Installed =="
