#!/usr/bin/env bash
# Control centre for the test VM. Everything you need day to day, in one place.
#
#   ./vmctl.sh start|stop|kill|status|ip|ssh [cmd...]|shot [file]|console|viewer
#   ./vmctl.sh snap create <name> | snap list | snap revert <name> | snap rm <name>
#   ./vmctl.sh reset          # back to the snapshot 'clean'
#   ./vmctl.sh push <source> <target>
#
# Principle: this VM is a disposable target. 'reset' is the normal case,
# not the exception - every theme test starts from a clean snapshot.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Which VM? The default is the Fedora machine from lab.env.
#
# Since there is a second one (EndeavourOS, for the Arch side of the scripts)
# LAB_ENV selects the environment:
#
#   ./vmctl.sh status                      # Fedora
#   LAB_ENV=eos.env ./vmctl.sh status      # EndeavourOS
#
# A second copy of this script would have been the obvious solution
# - and the worse one: every fix would then have to be made in two
# places, and that is exactly what gets forgotten.
LAB_ENV_FILE="${LAB_ENV:-lab.env}"
case "$LAB_ENV_FILE" in
    /*) source "$LAB_ENV_FILE" ;;
    *)  source "$VM_DIR/$LAB_ENV_FILE" ;;
esac

V() { virsh -c "$LIBVIRT_URI" "$@"; }

die() { echo "ERROR: $*" >&2; exit 1; }

vm_ip() {
    # First the guest agent (reliable), then the DHCP lease as a fallback.
    local ip
    ip=$(V domifaddr "$VM_NAME" --source agent 2>/dev/null \
         | awk '$3=="ipv4" && $4!~/^127\./ {sub(/\/.*/,"",$4); print $4; exit}')
    [ -n "$ip" ] || ip=$(V domifaddr "$VM_NAME" --source lease 2>/dev/null \
         | awk '$3=="ipv4" {sub(/\/.*/,"",$4); print $4; exit}')
    [ -n "$ip" ] || return 1
    echo "$ip"
}

wait_ssh() {
    local timeout="${1:-300}" waited=0 ip
    echo -n "Waiting for SSH" >&2
    while [ "$waited" -lt "$timeout" ]; do
        if ip=$(vm_ip 2>/dev/null) && \
           ssh $SSH_OPTS "$VM_USER@$ip" 'test -f /etc/plasma-lab-ready' 2>/dev/null; then
            echo " - ready ($ip)" >&2
            echo "$ip"
            return 0
        fi
        echo -n "." >&2
        sleep 5
        waited=$((waited + 5))
    done
    echo " - timed out" >&2
    return 1
}

# No screen lock, no dimming, no display off, no suspend: in a test VM they
# only give black screenshots or the lock screen (provision.sh sets the same;
# older snapshots such as 'clean' predate it, so it is set again after every
# start and revert). The running session picks it up at once.
lab_quiet() {
    local ip
    ip=$(vm_ip) || return 0
    ssh $SSH_OPTS "$VM_USER@$ip" 'export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
        kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
        kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume false
        for p in AC Battery LowBattery; do
            kwriteconfig6 --file powerdevilrc --group $p --group Display --key DimDisplayWhenIdle false
            kwriteconfig6 --file powerdevilrc --group $p --group Display --key TurnOffDisplayWhenIdle false
            kwriteconfig6 --file powerdevilrc --group $p --group SuspendAndShutdown --key AutoSuspendAction 0
        done
        dbus-send --session --type=method_call --dest=org.freedesktop.ScreenSaver /ScreenSaver org.kde.screensaver.configure 2>/dev/null
        systemctl --user try-restart plasma-powerdevil.service 2>/dev/null' >/dev/null 2>&1 || true
}

cmd="${1:-status}"
shift || true

case "$cmd" in

  start)
      V domstate "$VM_NAME" 2>/dev/null | grep -qE 'laufend|running' || V start "$VM_NAME"
      wait_ssh "${1:-300}" >/dev/null
      lab_quiet
      echo "VM is running."
      ;;

  stop)
      # Clean shutdown - important so that file system snapshots are consistent.
      V shutdown "$VM_NAME" 2>/dev/null || true
      for _ in $(seq 60); do
          V domstate "$VM_NAME" 2>/dev/null | grep -q 'ausgeschaltet\|shut off' && break
          sleep 2
      done
      V domstate "$VM_NAME"
      ;;

  kill)
      V destroy "$VM_NAME" 2>/dev/null || true
      echo "VM stopped hard."
      ;;

  status)
      V domstate "$VM_NAME" 2>/dev/null || die "VM '$VM_NAME' does not exist."
      vm_ip 2>/dev/null | sed 's/^/IP: /' || echo "IP: (none yet)"
      V snapshot-list "$VM_NAME" 2>/dev/null | tail -n +3 | grep -v '^$' | sed 's/^/Snapshot: /' || true
      ;;

  ip)
      vm_ip || die "No IP - is the VM running and the guest agent active?"
      ;;

  ssh)
      # The Plasma tools (plasma-apply-*, kquitapp6, plasmashell)
      # need a connection to the running session. An SSH session
      # does not have one - without DBUS_SESSION_BUS_ADDRESS, for example,
      # 'plasma-apply-lookandfeel' aborts with SIGABRT, and without any
      # useful message. That then looks like a theme bug.
      #
      # In this VM there is always exactly one session of uid 1000,
      # which is why the values are fixed.
      ip=$(vm_ip) || die "No IP."
      ENV_PREFIX='export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=KDE
'
      if [ $# -eq 0 ]; then
          exec ssh $SSH_OPTS "$VM_USER@$ip"
      else
          exec ssh $SSH_OPTS "$VM_USER@$ip" "$ENV_PREFIX$*"
      fi
      ;;

  push)
      # push <local-source> <target-in-guest>
      [ $# -eq 2 ] || die "Usage: $0 push <source> <target>"
      ip=$(vm_ip) || die "No IP."
      rsync -a --delete -e "ssh $SSH_OPTS" "$1" "$VM_USER@$ip:$2"
      ;;

  pull)
      [ $# -eq 2 ] || die "Usage: $0 pull <source-in-guest> <target>"
      ip=$(vm_ip) || die "No IP."
      rsync -a -e "ssh $SSH_OPTS" "$VM_USER@$ip:$1" "$2"
      ;;

  shot)
      # Screenshot via the hypervisor - works even when Plasma
      # has crashed or no session is running at all. That is exactly why
      # it is the right approach for theme tests.
      out="${1:-$VM_DIR/../tests/screenshots/shot-$(date +%Y%m%d-%H%M%S).png}"
      mkdir -p "$(dirname "$out")"
      tmp=$(mktemp --suffix=.ppm)
      V screenshot "$VM_NAME" "$tmp" >/dev/null
      if command -v magick &>/dev/null; then
          magick "$tmp" "$out"
      elif command -v convert &>/dev/null; then
          convert "$tmp" "$out"
      else
          out="${out%.png}.ppm"; cp "$tmp" "$out"
          echo "Note: ImageMagick is missing, saved PPM instead of PNG." >&2
      fi
      rm -f "$tmp"
      echo "$out"
      ;;

  console)
      exec virsh -c "$LIBVIRT_URI" console "$VM_NAME"
      ;;

  viewer)
      # --attach is mandatory here, not a matter of taste: the VM runs with
      # 'spice,listen=none', so SPICE does not listen on any network port.
      # Without --attach, virt-viewer tries a TCP connection and reports
      # "Connection failed"; with --attach it has libvirt hand it
      # the socket.
      exec virt-viewer --attach -c "$LIBVIRT_URI" "$VM_NAME"
      ;;

  viewer-bg)
      # Like 'viewer', but detached from the calling process group.
      # Needed when the call comes from a tool that cleans up its
      # process group after the command - neither nohup nor setsid
      # helps against that, but a systemd user unit of its own does.
      systemctl --user stop plasma-lab-viewer 2>/dev/null || true
      systemd-run --user --unit=plasma-lab-viewer --collect \
          --setenv=WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}" \
          --setenv=DISPLAY="${DISPLAY:-:0}" \
          --setenv=XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
          virt-viewer --attach -c "$LIBVIRT_URI" "$VM_NAME"
      ;;

  snap)
      sub="${1:-list}"; shift || true
      case "$sub" in
          create)
              name="${1:?snapshot name missing}"
              # An internal snapshot of the running VM including RAM would be faster,
              # but an offline snapshot is more reproducible: the same
              # starting state on every revert, no half-initialised session.
              V domstate "$VM_NAME" | grep -qE 'laufend|running' && { echo "Shutting down VM..."; "$0" stop >/dev/null; }
              V snapshot-create-as "$VM_NAME" "$name" "Snapshot $name" --atomic
              echo "Snapshot '$name' created."
              ;;
          list)   V snapshot-list "$VM_NAME" ;;
          revert)
              name="${1:?snapshot name missing}"
              V destroy "$VM_NAME" &>/dev/null || true
              V snapshot-revert "$VM_NAME" "$name" --running
              wait_ssh 300 >/dev/null
              lab_quiet
              echo "Reverted to '$name', VM is running."
              ;;
          rm)     V snapshot-delete "$VM_NAME" "${1:?name missing}" ;;
          *)      die "snap: unknown '$sub'" ;;
      esac
      ;;

  reset)
      exec "$0" snap revert clean
      ;;

  *)
      sed -n '2,20p' "$0"
      exit 1
      ;;
esac
