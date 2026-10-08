# plasma-theme-lab — Hinweise für Coding-Agenten

## VM-Speicherort (seit 25.09.2026)

Die Platte der VM `plasma-lab` liegt auf der großen Datenplatte:
`/data/vm/images/plasma-lab.qcow2` (ext4, `/dev/nvme0n1p1`). Vorher lag sie unter
`~/.local/share/libvirt/images/`; dort steht nur noch ein Symlink auf den neuen
Ort. Die libvirt-Definition (`qemu:///system`) und ihre Snapshots zeigen bereits
auf `/data`, ebenso `vm/lab.env (VM_DISK)`. Snapshots: `clean`, `icons-vorher`, `vor-boot`. Die EOS-VM (`vm/eos.env`) lag schon immer dort.
Seit 07.10.2026 gibt es eine dritte: `ubuntu-lab` (`vm/ubuntu.env`, Ubuntu
26.04 LTS + `kubuntu-desktop`, gebaut aus dem Cloud-Image per cloud-init mit
`vm/build-vm-ubuntu.sh`, unbeaufsichtigt). Aufruf: `LAB_ENV=ubuntu.env ./vmctl.sh …`.
Neue VM-Platten bitte ebenfalls nach `/data/vm/images/` legen, nicht auf die
Root-/Home-Partition (die war mit 98 % voll).

## Die Themes sind getrennt (seit 30.09.2026)

`nt-legacy/` und `CDE/` teilen sich das Repository, sonst nichts. Eine
Änderung an einem Theme darf das andere nicht verändern:

- CDE baut ausschließlich mit seinen eigenen Kopien der Generatoren unter
  `CDE/tools/` (Stand 9930435). Das gemeinsame `tools/` gehört NT Legacy.
  Kein Rückfall von `CDE/build.py` auf `../tools`, kein Verweis von
  `nt-legacy/` auf `CDE/`.
- Wer eine Verbesserung aus `tools/` auch in CDE haben will, kopiert sie
  bewusst nach `CDE/tools/`, baut neu und sieht sich den Diff in `CDE/build/`
  an. Nie umgekehrt stillschweigend.
- `CDE/tests/verify.py` baut das Theme aus einer Kopie ohne
  Elternverzeichnis nach und vergleicht byte-genau mit `CDE/build/`. Schlägt
  das fehl, ist die Trennung verletzt.
