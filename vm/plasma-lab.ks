# Kickstart: Plasma-Theme-Test-VM (Fedora 44 KDE, Plasma 6)
# Unattended-Installation, SSH-Zugang per Key, Autologin in die Plasma-Wayland-Session.
# Zweck: Wegwerf-Umgebung zum Testen von Plasma-Themes, inkl. SDDM/Plymouth/GRUB.

text
eula --agreed

# Das updates-Repo ist hier PFLICHT, nicht Kosmetik. Fedora 44 GA liefert
# kwin-6.7.4 zusammen mit kscreenlocker-6.6.4 aus - diese Kombination ist
# ABI-inkompatibel. kwin_wayland startet dann gar nicht:
#
#   kwin_wayland: symbol lookup error: /lib64/libkwin.so.6:
#   undefined symbol: ScreenLocker::KSldApp::inhibitSuspend()
#
# Ohne Compositor gibt es keine Wayland-Sitzung, und der Autologin laeuft
# in eine Endlosschleife. Der Fix (kscreenlocker-6.7.4) liegt in updates.
url --url=https://download.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os/
repo --name=updates --baseurl=https://download.fedoraproject.org/pub/fedora/linux/updates/44/Everything/x86_64/

lang de_DE.UTF-8
keyboard --vckeymap=de --xlayouts='de'
timezone Europe/Berlin --utc

# Netzwerk: DHCP über libvirt-default-NAT
network --bootproto=dhcp --device=link --activate --hostname=plasma-lab

# Speicher: alles löschen, simples Layout ohne LVM/Btrfs-Subvolumes
# (macht qcow2-Snapshots und Offline-Inspektion mit guestfish einfacher)
ignoredisk --only-use=vda
clearpart --all --initlabel --drives=vda
part /boot/efi --fstype=efi   --size=600  --ondisk=vda
part /boot     --fstype=ext4  --size=1024 --ondisk=vda
part /         --fstype=ext4  --grow      --ondisk=vda
bootloader --location=mbr --boot-drive=vda

# Zugänge: root gesperrt, ein Testnutzer mit sudo.
# Passwort ist bewusst trivial - die VM ist NAT-isoliert und ein Wegwerf-Ziel.
rootpw --lock
user --name=tester --groups=wheel --password=tester --plaintext --gecos="Theme Tester"
sshkey --username=tester "SSH_PUBKEY_PLACEHOLDER"

selinux --enforcing
firewall --disabled
# sddm bewusst NICHT hier: Fedora 44 liefert den Plasma Login Manager
# (plasmalogin) statt SDDM aus. Der Login-Manager wird im %post erkannt.
services --enabled=sshd,qemu-guest-agent
skipx

reboot

# Bewusst minimal gehalten. Jedes zusätzliche Paket hier ist eine
# mögliche Abbruchstelle in einer unbeaufsichtigten Installation - ein
# Tippfehler im Paketnamen bringt Anaconda zum Stehen, und das ist in
# einer VM ohne Bildschirmzugriff mühsam zu finden. Alle Testwerkzeuge
# installiert stattdessen provision.sh nach, wo ein Fehler sichtbar und
# ohne Neuinstallation behebbar ist.
#
# --ignoremissing: lieber ein fehlendes Paket als eine hängende Installation.
%packages --ignoremissing
@^kde-desktop-environment
openssh-server
qemu-guest-agent
%end

%post --log=/root/ks-post.log
set -x

# --- Autologin in die Plasma-Wayland-Session -------------------------------
# Ohne Autologin gibt es keine laufende Plasma-Session, gegen die man
# plasma-apply-* aufrufen oder Screenshots machen kann.
#
# Fedora 44 hat SDDM durch den Plasma Login Manager (plasmalogin) ersetzt.
# Beide werden hier bedient, damit das Kickstart auch auf aelteren
# Fedora-Versionen funktioniert - der jeweils nicht vorhandene Teil
# ist einfach eine ungenutzte Konfigurationsdatei.

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

# --- SSH: Key-Login, Passwort-Login zusätzlich erlauben ---------------------
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/10-lab.conf <<'EOF'
PasswordAuthentication yes
PermitRootLogin no
EOF

# --- sudo ohne Passwort: der Testharness fasst SDDM/Plymouth/GRUB an -------
echo 'tester ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/90-tester
chmod 440 /etc/sudoers.d/90-tester

# --- Marker, an dem der Host erkennt, dass die Installation durch ist ------
echo "plasma-lab ready $(date -Is)" > /etc/plasma-lab-ready

# --- Baseline der theme-relevanten Systempfade sichern ---------------------
# Erlaubt später ein Diff "was hat der Installer am System verändert?"
mkdir -p /var/lib/plasma-lab
{
  echo "# Baseline der theme-relevanten Systempfade"
  ls -1 /usr/share/plasma/desktoptheme/     2>/dev/null | sed 's|^|desktoptheme/|'
  ls -1 /usr/share/plasma/look-and-feel/    2>/dev/null | sed 's|^|look-and-feel/|'
  ls -1 /usr/share/sddm/themes/             2>/dev/null | sed 's|^|sddm/|'
  ls -1 /usr/share/plymouth/themes/         2>/dev/null | sed 's|^|plymouth/|'
  ls -1 /usr/share/aurorae/themes/          2>/dev/null | sed 's|^|aurorae/|'
} > /var/lib/plasma-lab/baseline.txt

%end
