# plasma-theme-lab — notes for coding agents

## VM location (since 25.09.2026)

The disk of the VM `plasma-lab` lives on the large data disk:
`/data/vm/images/plasma-lab.qcow2` (ext4, `/dev/nvme0n1p1`). It used to live under
`~/.local/share/libvirt/images/`; only a symlink to the new location remains
there. The libvirt definition (`qemu:///system`) and its snapshots already point
to `/data`, as does `vm/lab.env (VM_DISK)`. Snapshots: `clean`, `icons-vorher`, `vor-boot`. The EOS VM (`vm/eos.env`) has always lived there.
Since 07.10.2026 there is a third one: `ubuntu-lab` (`vm/ubuntu.env`, Ubuntu
26.04 LTS + `kubuntu-desktop`, built from the cloud image via cloud-init with
`vm/build-vm-ubuntu.sh`, unattended). Usage: `LAB_ENV=ubuntu.env ./vmctl.sh …`.
Please put new VM disks in `/data/vm/images/` as well, not on the
root/home partition (it was 98 % full).

## The themes are separate (since 30.09.2026)

`nt-legacy/` and `CDE/` share the repository, nothing else. A
change to one theme must not alter the other:

- CDE builds exclusively with its own copies of the generators under
  `CDE/tools/` (as of 9930435). The shared `tools/` belongs to NT Legacy.
  No fallback from `CDE/build.py` to `../tools`, no reference from
  `nt-legacy/` to `CDE/`.
- Anyone who wants an improvement from `tools/` in CDE as well copies it
  deliberately to `CDE/tools/`, rebuilds and reviews the diff in `CDE/build/`.
  Never silently the other way round.
- `CDE/tests/verify.py` rebuilds the theme from a copy without its
  parent directory and compares byte for byte with `CDE/build/`. If that
  fails, the separation has been broken.
