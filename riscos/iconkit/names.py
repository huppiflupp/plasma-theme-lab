#!/usr/bin/env python3
"""Which icons a complete theme needs, and which names mean the same.

Breeze is the measure (the user's wish 25.10.2026: every icon, no
duplicates). Its files are the meanings; its symlinks are synonyms of
the file they point to. Across Breeze's size folders a name can be a file
in one and a link in another: a link anywhere makes it a synonym.
"-symbolic" names (monochrome variants Plasma recolours) and "-rtl"
mirrors are left out; Breeze answers for those.

    names.py [BREEZE]     prints a summary; names() returns
                          {category: {meaning: [synonym, ...]}}
"""
import json
import os
import sys
from pathlib import Path

BREEZE = Path("/usr/share/icons/breeze")
CATEGORIES = ("places", "devices", "mimetypes", "categories", "emblems", "apps", "preferences",
              "status", "emotes", "actions")


def _skip(name):
    return name.endswith("-symbolic") or name.endswith("-rtl") or name.endswith("-symbolic-rtl")


def names(breeze=BREEZE):
    # Every file and link in every size folder: name -> (category, target
    # category, target name) for links, the set of (category, name) files.
    files, links = set(), {}
    # Per name only its largest size counts: Breeze's 16/22 px folders link
    # many names to monochrome actions (places/16/user-home -> actions/16/
    # go-home) to save drawing; that is no sameness of meaning.
    best = {}
    for cat in CATEGORIES:
        for d in sorted((breeze / cat).iterdir()):
            if not d.is_dir() or not d.name.isdigit():
                continue
            size = int(d.name)
            for f in d.glob("*.svg"):
                n = f.stem
                if _skip(n):
                    continue
                if size >= best.get((cat, n), (0, None))[0]:
                    best[(cat, n)] = (size, f)
    for (cat, n), (_, f) in best.items():
        if f.is_symlink():
            target = Path(os.path.normpath(f.parent / os.readlink(f)))
            tcat = target.parent.parent.name if target.parent.parent.name in CATEGORIES else cat
            links[(cat, n)] = (tcat, target.stem)
        else:
            files.add((cat, n))

    def root(key, seen=()):
        t = links.get(key)
        if t is None or t in seen:
            return key
        return root(t, seen + (key,))

    result = {cat: {} for cat in CATEGORIES}
    for cat, n in sorted(files):
        if (cat, n) not in links:
            result[cat].setdefault(n, [])
    # Links: synonyms of the meaning they lead to, in its category; a link
    # to another category (mimetypes/inode-directory -> places/folder) is
    # a synonym there.
    for (cat, n), _ in sorted(links.items()):
        rcat, rn = root((cat, n))
        if _skip(rn) or rn == n:
            # Leads to a -symbolic variant (Breeze's small sizes) or round in
            # a circle: the name is a meaning of its own where it is a file.
            if (cat, n) in files:
                result[cat].setdefault(n, [])
            continue
        if rn in result.get(rcat, {}):
            result[rcat][rn].append(n)
        elif (rcat, rn) in files:
            result[rcat].setdefault(rn, []).append(n)
        else:
            result[cat].setdefault(n, [])
    # A name in several categories keeps the first; synonyms never repeat a
    # meaning or another synonym.
    seen = set()
    for cat in CATEGORIES:
        for k in list(result[cat]):
            if k in seen:
                del result[cat][k]
            else:
                seen.add(k)
    for cat in CATEGORIES:
        for k, syn in result[cat].items():
            result[cat][k] = sorted({s for s in syn if s not in seen or s == k} - {k})
            seen.update(result[cat][k])
    return {cat: dict(sorted(m.items())) for cat, m in result.items()}


if __name__ == "__main__":
    r = names(Path(sys.argv[1]) if len(sys.argv) > 1 else BREEZE)
    total = 0
    for cat, m in r.items():
        syn = sum(len(v) for v in m.values())
        total += len(m)
        print(f"{cat:12} {len(m):5} meanings {syn:5} synonyms")
    print(f"{'total':12} {total:5}")
    Path("/tmp/claude-1000").mkdir(exist_ok=True)
