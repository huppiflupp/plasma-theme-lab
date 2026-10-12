# Kickstart: Plasma theme test VM (Fedora 44 KDE, Plasma 6)
# Unattended installation, SSH access by key, autologin into the Plasma Wayland session.
# Purpose: disposable environment for testing Plasma themes, incl. SDDM/Plymouth/GRUB.

text
eula --agreed

# The updates repo is MANDATORY here, not cosmetic. Fedora 44 GA ships
# kwin-6.7.4 together with kscreenlocker-6.6.4 - this combination is
# ABI-incompatible. kwin_wayland then does not start at all:
#
#   kwin_wayland: symbol lookup error: /lib64/libkwin.so.6:
#   undefined symbol: ScreenLocker::KSldApp::inhibitSuspend()
#
# Without a compositor there is no Wayland session, and the autologin runs
# into an endless loop. The fix (kscreenlocker-6.7.4) is in updates.
url --url=https://download.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os/
repo --name=updates --baseurl=https://download.fedoraproject.org/pub/fedora/linux/updates/44/Everything/x86_64/

lang de_DE.UTF-8
keyboard --vckeymap=de --xlayouts='de'
timezone Europe/Berlin --utc

# Network: DHCP via the libvirt default NAT
network --bootproto=dhcp --device=link --activate --hostname=plasma-lab

# Storage: wipe everything, simple layout without LVM/Btrfs subvolumes
# (makes qcow2 snapshots and offline inspection with guestfish easier)
ignoredisk --only-use=vda
clearpart --all --initlabel --drives=vda
part /boot/efi --fstype=efi   --size=600  --ondisk=vda
part /boot     --fstype=ext4  --size=1024 --ondisk=vda
part /         --fstype=ext4  --grow      --ondisk=vda
bootloader --location=mbr --boot-drive=vda

# Access: root locked, one test user with sudo.
# The password is deliberately trivial - the VM is NAT-isolated and a disposable target.
rootpw --lock
user --name=tester --groups=wheel --password=tester --plaintext --gecos="Theme Tester"
sshkey --username=tester "SSH_PUBKEY_PLACEHOLDER"

selinux --enforcing
firewall --disabled
# sddm deliberately NOT here: Fedora 44 ships the Plasma Login Manager
# (plasmalogin) instead of SDDM. The login manager is detected in %post.
services --enabled=sshd,qemu-guest-agent
skipx

reboot

# Deliberately kept minimal. Every additional package here is a
# possible point of failure in an unattended installation - a
# typo in a package name brings Anaconda to a halt, and that is
# tedious to find in a VM without screen access. All test tools are
# installed by provision.sh instead, where an error is visible and
# can be fixed without reinstalling.
#
# --ignoremissing: better a missing package than a hanging installation.
%packages --ignoremissing
@^kde-desktop-environment
openssh-server
qemu-guest-agent
%end

%post --log=/root/ks-post.log
set -x

# --- Autologin into the Plasma Wayland session ------------------------------
# Without autologin there is no running Plasma session against which
# plasma-apply-* can be called or screenshots taken.
#
# Fedora 44 replaced SDDM with the Plasma Login Manager (plasmalogin).
# Both are handled here so that the kickstart also works on older
# Fedora versions - the part that is not present in each case
# is simply an unused configuration file.

# Plasma Login Manager (Fedora 44+)
if [ -f /usr/lib/systemd/system/plasmalogin.service ]; then
    mkdir -p /etc/plasmalogin.conf.d
    cat > /etc/plasmalogin.conf.d/10-autologin.conf <<'EOF'
[Autologin]
User=tester
Session=plasma.desktop
Relogin=true
EOF
    systemctl enable plasmalogin.service
fi

# SDDM (Fedora <= 43)
if [ -f /usr/lib/systemd/system/sddm.service ]; then
    mkdir -p /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/10-autologin.conf <<'EOF'
[Autologin]
User=tester
Session=plasma
Relogin=true
EOF
    systemctl enable sddm.service
fi

systemctl set-default graphical.target

# --- SSH: key login, additionally allow password login ----------------------
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/10-lab.conf <<'EOF'
PasswordAuthentication yes
PermitRootLogin no
EOF

# --- sudo without password: the test harness touches SDDM/Plymouth/GRUB ----
echo 'tester ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/90-tester
chmod 440 /etc/sudoers.d/90-tester

# --- Marker by which the host recognises that the installation is done ----
echo "plasma-lab ready $(date -Is)" > /etc/plasma-lab-ready

# --- Save a baseline of the theme-relevant system paths --------------------
# Allows a later diff "what did the installer change on the system?"
mkdir -p /var/lib/plasma-lab
{
  echo "# Baseline of the theme-relevant system paths"
  ls -1 /usr/share/plasma/desktoptheme/     2>/dev/null | sed 's|^|desktoptheme/|'
  ls -1 /usr/share/plasma/look-and-feel/    2>/dev/null | sed 's|^|look-and-feel/|'
  ls -1 /usr/share/sddm/themes/             2>/dev/null | sed 's|^|sddm/|'
  ls -1 /usr/share/plymouth/themes/         2>/dev/null | sed 's|^|plymouth/|'
  ls -1 /usr/share/aurorae/themes/          2>/dev/null | sed 's|^|aurorae/|'
} > /var/lib/plasma-lab/baseline.txt

%end
