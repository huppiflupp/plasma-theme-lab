#!/usr/bin/env python3
"""Decode RISC OS sprite files (,ff9) to PNG.

rospr.py sheet FILE OUT.png      contact sheet of all sprites, names below
rospr.py dump FILE OUTDIR        one PNG per sprite (RGBA)
"""
import struct, sys, os
from PIL import Image, ImageDraw

WIMP16 = [0xFFFFFF, 0xDDDDDD, 0xBBBBBB, 0x999999, 0x777777, 0x555555, 0x333333, 0x000000,
          0x004499, 0xEEEE00, 0x00CC00, 0xDD0000, 0xEEEEBB, 0x558800, 0xFFBB00, 0x00BBFF]
MONO = [0xFFFFFF, 0x000000]
GREY4 = [0xFFFFFF, 0xBBBBBB, 0x777777, 0x000000]

def default256(c):
    t = c & 3
    r = ((c >> 4) & 1) << 3 | ((c >> 2) & 1) << 2 | t
    g = ((c >> 6) & 1) << 3 | ((c >> 5) & 1) << 2 | t
    b = ((c >> 7) & 1) << 3 | ((c >> 3) & 1) << 2 | t
    return (r * 17) << 16 | (g * 17) << 8 | (b * 17)

# old screen modes -> bits per pixel, x/y eig
MODE_BPP = {0: 1, 1: 2, 2: 4, 3: 1, 4: 1, 5: 2, 6: 1, 7: 4, 8: 2, 9: 4, 10: 8, 11: 2, 12: 4, 13: 8,
            14: 4, 15: 8, 16: 4, 17: 4, 18: 1, 19: 2, 20: 4, 21: 8, 22: 4, 23: 1, 24: 8, 25: 1,
            26: 2, 27: 4, 28: 8, 29: 1, 30: 2, 31: 4, 32: 8, 33: 1, 34: 2, 35: 4, 36: 8, 37: 1,
            38: 2, 39: 4, 40: 8, 41: 1, 42: 2, 43: 4, 44: 1, 45: 2, 46: 4, 47: 8, 48: 4, 49: 8}
# modes with 2:1 pixels (y eig 2): low-res modes; tool sprites use 1:1 in 22 or 2:1 in non-22 files
TYPE_BPP = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32, 7: 32, 8: 24, 10: 16}

def read_sprites(data):
    count, first, free = struct.unpack_from("<iii", data, 0)
    off = first - 4
    out = []
    for _ in range(count):
        nxt, = struct.unpack_from("<i", data, off)
        name = data[off + 4:off + 16].split(b"\0")[0].decode("latin-1")
        wwords, hm1, fbit, lbit, img, msk, mode = struct.unpack_from("<iiiiiii", data, off + 16)
        out.append(decode(data, off, name, wwords, hm1, fbit, lbit, img, msk, mode))
        off += nxt
    return out

def decode(data, base, name, wwords, hm1, fbit, lbit, img, msk, mode):
    new = mode > 255
    alpha_mask = False
    if new:
        mtype = (mode >> 27) & 31
        if mtype == 15:  # RISC OS 5 extended mode word
            mtype = (mode >> 20) & 127
            alpha_mask = bool(mode & 0x80000000)
        else:
            alpha_mask = bool(mode & 0x80000000)
        bpp = TYPE_BPP.get(mtype, 32)
        ydpi = (mode >> 14) & 0x1FFF
        xdpi = (mode >> 1) & 0x1FFF
        yeig = 2 if ydpi and ydpi < 90 else 1
        xeig = 2 if xdpi and xdpi < 90 else 1
    else:
        bpp = MODE_BPP.get(mode, 4)
        yeig = 2 if mode in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 24, 33, 34, 35, 36) else 1
        xeig = 2 if mode in (1, 2, 4, 5, 9, 10, 13) else 1
    rowbytes = (wwords + 1) * 4
    h = hm1 + 1
    w = ((wwords + 1) * 32 - fbit - (31 - lbit)) // bpp
    # palette
    pal = None
    if img > 44 and bpp <= 8:
        n = (img - 44) // 8
        pal = []
        for i in range(n):
            v, = struct.unpack_from("<I", data, base + 44 + i * 8)
            pal.append(((v >> 8) & 0xFF) << 16 | ((v >> 16) & 0xFF) << 8 | ((v >> 24) & 0xFF))
    if pal is None:
        pal = {1: MONO, 2: GREY4, 4: WIMP16}.get(bpp)
    im = Image.new("RGBA", (w, h))
    px = im.load()
    for y in range(h):
        row = base + img + y * rowbytes
        for x in range(w):
            bit = fbit + x * bpp
            if bpp >= 8:
                o = row + bit // 8
                if bpp == 8:
                    c = data[o]
                    rgb = pal[c] if pal and c < len(pal) else default256(c)
                elif bpp == 16:
                    v = data[o] | data[o + 1] << 8
                    r, g, b = v & 31, (v >> 5) & 31, (v >> 10) & 31
                    rgb = (r * 255 // 31) << 16 | (g * 255 // 31) << 8 | (b * 255 // 31)
                else:
                    r, g, b = data[o], data[o + 1], data[o + 2]
                    rgb = r << 16 | g << 8 | b
            else:
                byte = data[row + bit // 8]
                c = (byte >> (bit % 8)) & ((1 << bpp) - 1)
                rgb = pal[c % len(pal)]
            px[x, y] = (rgb >> 16 & 255, rgb >> 8 & 255, rgb & 255, 255)
    if msk != img:
        if new and alpha_mask:
            mrow = (w + 3) // 4 * 4
            for y in range(h):
                for x in range(w):
                    a = data[base + msk + y * mrow + x]
                    r, g, b, _ = px[x, y]; px[x, y] = (r, g, b, a)
        elif new:
            mrow = ((w + 31) // 32) * 4
            for y in range(h):
                for x in range(w):
                    if not (data[base + msk + y * mrow + x // 8] >> (x % 8)) & 1:
                        px[x, y] = (0, 0, 0, 0)
        else:
            for y in range(h):
                for x in range(w):
                    bit = fbit + x * bpp
                    byte = data[base + msk + y * rowbytes + bit // 8]
                    if not (byte >> (bit % 8)) & ((1 << bpp) - 1):
                        px[x, y] = (0, 0, 0, 0)
    return {"name": name, "image": im, "bpp": bpp, "eig": (xeig, yeig), "mode": mode}

def square(s):
    """Scale to square pixels (old low-res sprites are 2:1)."""
    im = s["image"]
    xe, ye = s["eig"]
    if ye > xe:
        im = im.resize((im.width, im.height * 2), Image.NEAREST)
    return im

def sheet(path, out, scale=3):
    sp = read_sprites(open(path, "rb").read())
    cell = 0
    ims = [square(s) for s in sp]
    ims = [i.crop((0, 0, min(i.width, 48), min(i.height, 48))) for i in ims]
    cw = max(max(i.width for i in ims) * scale, 110) + 10
    ch = max(i.height for i in ims) * scale + 26
    cols = max(1, min(10, 1400 // cw))
    rows = (len(sp) + cols - 1) // cols
    W, H = cols * cw, rows * ch
    bg = Image.new("RGB", (W, H), (120, 140, 150))
    d = ImageDraw.Draw(bg)
    sizes = [square(s).size for s in sp]
    for k, (s, im) in enumerate(zip(sp, ims)):
        x, y = (k % cols) * cw + 5, (k // cols) * ch + 4
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        bg.paste(big, (x, y), big)
        d.text((x, y + big.height + 2), f"{s['name']} {sizes[k][0]}x{sizes[k][1]}", fill=(255, 255, 255))
    bg.save(out)
    print(out, len(sp), "sprites")

def dump(path, outdir):
    os.makedirs(outdir, exist_ok=True)
    for s in read_sprites(open(path, "rb").read()):
        square(s).save(os.path.join(outdir, s["name"] + ".png"))

if __name__ == "__main__":
    {"sheet": sheet, "dump": dump}[sys.argv[1]](*sys.argv[2:])
