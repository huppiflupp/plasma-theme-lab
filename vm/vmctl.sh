#!/usr/bin/env bash
# Steuerzentrale der Test-VM. Alles, was man im Alltag braucht, an einer Stelle.
#
#   ./vmctl.sh start|stop|kill|status|ip|ssh [cmd...]|shot [datei]|console|viewer
#   ./vmctl.sh snap create <name> | snap list | snap revert <name> | snap rm <name>
#   ./vmctl.sh reset          # zurueck auf den Snapshot 'clean'
#   ./vmctl.sh push <quelle> <ziel>
#
# Grundsatz: Diese VM ist ein Wegwerf-Ziel. 'reset' ist der Normalfall,
# nicht die Ausnahme - jeder Theme-Test startet von einem sauberen Snapshot.

set -euo pipefail

VM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$VM_DIR/lab.env"

V() { virsh -c "$LIBVIRT_URI" "$@"; }

die() { echo "FEHLER: $*" >&2; exit 1; }

vm_ip() {
    # Zuerst der Guest-Agent (zuverlaessig), dann der DHCP-Lease als Rueckfall.
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
    echo -n "Warte auf SSH" >&2
    while [ "$waited" -lt "$timeout" ]; do
        if ip=$(vm_ip 2>/dev/null) && \
           ssh $SSH_OPTS "$VM_USER@$ip" 'test -f /etc/plasma-lab-ready' 2>/dev/null; then
            echo " - bereit ($ip)" >&2
            echo "$ip"
            return 0
        fi
        echo -n "." >&2
        sleep 5
        waited=$((waited + 5))
    done
    echo " - Zeitueberschreitung" >&2
    return 1
}

cmd="${1:-status}"
shift || true

case "$cmd" in

  start)
      V domstate "$VM_NAME" 2>/dev/null | grep -q laufend || V start "$VM_NAME"
      wait_ssh "${1:-300}" >/dev/null
      echo "VM laeuft."
      ;;

  stop)
      # Sauberes Herunterfahren - wichtig, damit Dateisystem-Snapshots konsistent sind.
      V shutdown "$VM_NAME" 2>/dev/null || true
      for _ in $(seq 60); do
          V domstate "$VM_NAME" 2>/dev/null | grep -q 'ausgeschaltet\|shut off' && break
          sleep 2
      done
      V domstate "$VM_NAME"
      ;;

  kill)
      V destroy "$VM_NAME" 2>/dev/null || true
      echo "VM hart gestoppt."
      ;;

  status)
      V domstate "$VM_NAME" 2>/dev/null || die "VM '$VM_NAME' existiert nicht."
      vm_ip 2>/dev/null | sed 's/^/IP: /' || echo "IP: (noch keine)"
      V snapshot-list "$VM_NAME" 2>/dev/null | tail -n +3 | grep -v '^$' | sed 's/^/Snapshot: /' || true
      ;;

  ip)
      vm_ip || die "Keine IP - laeuft die VM und ist der Guest-Agent aktiv?"
      ;;

  ssh)
      # Die Plasma-Werkzeuge (plasma-apply-*, kquitapp6, plasmashell)
      # brauchen eine Verbindung zur laufenden Sitzung. Eine SSH-Sitzung
      # hat die nicht - ohne DBUS_SESSION_BUS_ADDRESS bricht etwa
      # 'plasma-apply-lookandfeel' mit SIGABRT ab, und zwar ohne
      # brauchbare Meldung. Das sieht dann aus wie ein Theme-Fehler.
      #
      # In dieser VM laeuft immer genau eine Sitzung von uid 1000,
      # deshalb sind die Werte fest.
      ip=$(vm_ip) || die "Keine IP."
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
      # push <lokale-quelle> <ziel-im-gast>
      [ $# -eq 2 ] || die "Aufruf: $0 push <quelle> <ziel>"
      ip=$(vm_ip) || die "Keine IP."
      rsync -a --delete -e "ssh $SSH_OPTS" "$1" "$VM_USER@$ip:$2"
      ;;

  pull)
      [ $# -eq 2 ] || die "Aufruf: $0 pull <quelle-im-gast> <ziel>"
      ip=$(vm_ip) || die "Keine IP."
      rsync -a -e "ssh $SSH_OPTS" "$VM_USER@$ip:$1" "$2"
      ;;

  shot)
      # Screenshot ueber den Hypervisor - funktioniert auch, wenn Plasma
      # abgestuerzt ist oder gar keine Session mehr laeuft. Genau deshalb
      # ist das der richtige Weg fuer Theme-Tests.
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
          echo "Hinweis: ImageMagick fehlt, PPM statt PNG gespeichert." >&2
      fi
      rm -f "$tmp"
      echo "$out"
      ;;

  console)
      exec virsh -c "$LIBVIRT_URI" console "$VM_NAME"
      ;;

  viewer)
      # --attach ist hier Pflicht, nicht Geschmackssache: die VM laeuft mit
      # 'spice,listen=none', SPICE lauscht also auf keinem Netzwerk-Port.
      # Ohne --attach versucht virt-viewer eine TCP-Verbindung und meldet
      # "Verbindung fehlgeschlagen"; mit --attach laesst es sich den
      # Socket von libvirt reichen.
      exec virt-viewer --attach -c "$LIBVIRT_URI" "$VM_NAME"
      ;;

  viewer-bg)
      # Wie 'viewer', aber abgeloest von der aufrufenden Prozessgruppe.
      # Noetig, wenn der Aufruf aus einem Werkzeug kommt, das seine
      # Prozessgruppe nach dem Befehl abraeumt - dagegen helfen weder
      # nohup noch setsid, wohl aber eine eigene systemd-User-Unit.
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
              name="${1:?Name des Snapshots fehlt}"
              # Interner Snapshot bei laufender VM inkl. RAM waere schneller,
              # aber ein Offline-Snapshot ist reproduzierbarer: gleicher
              # Startzustand bei jedem Revert, keine halb-initialisierte Session.
              V domstate "$VM_NAME" | grep -q laufend && { echo "Fahre VM herunter..."; "$0" stop >/dev/null; }
              V snapshot-create-as "$VM_NAME" "$name" "Snapshot $name" --atomic
              echo "Snapshot '$name' erstellt."
              ;;
          list)   V snapshot-list "$VM_NAME" ;;
          revert)
              name="${1:?Name des Snapshots fehlt}"
              V destroy "$VM_NAME" &>/dev/null || true
              V snapshot-revert "$VM_NAME" "$name" --running
              wait_ssh 300 >/dev/null
              echo "Auf '$name' zurueckgesetzt, VM laeuft."
              ;;
          rm)     V snapshot-delete "$VM_NAME" "${1:?Name fehlt}" ;;
          *)      die "snap: unbekannt '$sub'" ;;
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
