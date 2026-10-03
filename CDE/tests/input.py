#!/usr/bin/env python3
"""VM-only virtual pointer/keyboard for testing the actual Wayland desktop."""
import argparse
import fcntl
import os
import struct
import time

ap = argparse.ArgumentParser()
ap.add_argument("action", choices=("click", "rightclick", "move", "key"))
ap.add_argument("values", nargs="+", type=int)
args = ap.parse_args()
fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
fcntl.ioctl(fd, 0x40045564, 1)  # EV_KEY
fcntl.ioctl(fd, 0x40045564, 3)  # EV_ABS
for code in (272, 273, 1, 15, 28, 57, 103, 108, 105, 106):
    fcntl.ioctl(fd, 0x40045565, code)
for code in (0, 1):
    fcntl.ioctl(fd, 0x40045567, code)
maximum = [0] * 64
maximum[0] = 32767
maximum[1] = 32767
data = struct.pack("80sHHHHI", b"CDE VM Test Pointer", 3, 0x1234, 1, 1, 0)
data += struct.pack("256i", *(maximum + [0] * 192))
os.write(fd, data)
fcntl.ioctl(fd, 0x5501)
time.sleep(0.6)


def event(kind, code, value):
    os.write(fd, struct.pack("llHHi", 0, 0, kind, code, value))


def sync():
    event(0, 0, 0)


if args.action == "key":
    key = args.values[0]
    event(1, key, 1); sync(); time.sleep(0.05)
    event(1, key, 0); sync()
else:
    x, y, width, height = args.values
    event(3, 0, round(x / width * 32767))
    event(3, 1, round(y / height * 32767))
    sync()
    time.sleep(0.25)
    if args.action in ("click", "rightclick"):
        button = 272 if args.action == "click" else 273
        event(1, button, 1); sync(); time.sleep(0.08)
        event(1, button, 0); sync()
time.sleep(0.3)
fcntl.ioctl(fd, 0x5502)
os.close(fd)
