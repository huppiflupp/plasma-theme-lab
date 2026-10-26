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
Since 26.10.2026 there is a fourth one: `artix-lab` (`vm/artix.env`, Artix Linux with
OpenRC and Plasma 6.8, **no systemd** - it is the test bed for the install scripts'
non-systemd branches). Built unattended by `vm/build-vm-artix.sh` from the official
base ISO (in `/data/vm/iso/artix/`); all packages come from Artix's dated archive
(`ARTIX_ARCHIVE_DATE`), so a rebuild gives the same versions. Like the others it has
no internet; the build reaches the archive through `vm/connect-proxy.py` and an SSH
reverse tunnel. Without systemd the session bus is not at `/run/user/1000/bus`; the
session writes its address to `/run/user/1000/bus-address`, which `vmctl.sh ssh`
reads. Usage: `LAB_ENV=artix.env ./vmctl.sh …`; snapshot `clean`. Theme Forge
tests in all three (Fedora, Ubuntu, Artix) with `forge.py vmtest out/<x>`.
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
