#!/usr/bin/env python3
"""Erzeugt eine Aurorae-Fensterdekoration aus Parametern.

Aurorae ist die SVG-basierte Dekorations-Engine von KWin. Eine
Dekoration besteht aus:

    decoration.svg   9-Patch fuer aktiv, inaktiv und maximiert
    close/maximize/minimize/restore.svg   je fuenf Zustaende
    <Name>rc         Geometrie: Rahmenbreiten, Titelhoehe, Buttons
    metadata.desktop Registrierung bei KWin

Die Element-IDs sind der Vertrag mit KWin - fehlt einer, zeichnet
KWin an der Stelle nichts, ohne Fehlermeldung.

    ./gen-aurorae.py --name NTLegacy -o nt-legacy/aurorae/
"""

import argparse
from pathlib import Path

# Aurorae kennt genau diese Zustandssaetze in der Dekoration.
# maximized-* wird gezeichnet, wenn das Fenster maximiert ist -
# dort entfaellt der Rahmen, nur die Titelleiste bleibt.
DEKO_SAETZE = ["decoration", "decoration-inactive"]
BUTTON_ZUSTAENDE = ["active", "inactive", "hover", "pressed", "deactivated"]
BUTTONS = ["close", "maximize", "minimize", "restore", "alldesktops",
           "keepabove", "keepbelow", "shade", "help", "menu"]


class Aurorae:
    def __init__(self, palette, titelhoehe=22, rahmen=4, aussen=1,
                 bevel=1, buttongroesse=14):
        self.p = palette
        self.th = titelhoehe
        self.rahmen = rahmen
        self.aussen = aussen
        self.bevel = bevel
        self.bg = buttongroesse

    def f(self, *keys):
        for k in keys:
            if k in self.p:
                return self.p[k]
        return "#000000"

    # ------------------------------------------------------------------
    def _patch(self, praefix, ox, oy, breite, hoehe, titel, flaeche):
        """Ein 9-Patch fuer die Dekoration.

        Oben liegt die Titelleiste in Volltonfarbe, an den uebrigen
        Seiten nur der Rahmen. Die Ecken oben gehoeren zur Titelleiste,
        die unteren zum Rahmen - sonst bricht die Titelleiste optisch
        an den Seiten ab.
        """
        r, a, b = self.rahmen, self.aussen, self.bevel
        aussenfarbe = self.f("rahmen")
        hell, dunkel = self.f("hell"), self.f("dunkel")
        t = []

        def rect(x, y, w, h, farbe):
            if w > 0 and h > 0:
                t.append(f'    <rect x="{x:g}" y="{y:g}" width="{w:g}" '
                         f'height="{h:g}" fill="{farbe}"/>')

        def feld(name, x, y, w, h, grund, kanten):
            t.append(f'  <g id="{praefix}-{name}">')
            rect(x, y, w, h, grund)
            # Aussenrahmen
            if "t" in kanten: rect(x, y, w, a, aussenfarbe)
            if "b" in kanten: rect(x, y + h - a, w, a, aussenfarbe)
            if "l" in kanten: rect(x, y, a, h, aussenfarbe)
            if "r" in kanten: rect(x + w - a, y, a, h, aussenfarbe)
            # 3D-Kante innen davon
            if "t" in kanten: rect(x + (a if "l" in kanten else 0), y + a,
                                   w - (a if "l" in kanten else 0) - (a if "r" in kanten else 0), b, hell)
            if "l" in kanten: rect(x + a, y + (a if "t" in kanten else 0), b,
                                   h - (a if "t" in kanten else 0) - (a if "b" in kanten else 0), hell)
            if "b" in kanten: rect(x + (a if "l" in kanten else 0), y + h - a - b,
                                   w - (a if "l" in kanten else 0) - (a if "r" in kanten else 0), b, dunkel)
            if "r" in kanten: rect(x + w - a - b, y + (a if "t" in kanten else 0), b,
                                   h - (a if "t" in kanten else 0) - (a if "b" in kanten else 0), dunkel)
            t.append('  </g>')

        th = self.th
        mitte_h = hoehe - th - r
        # Titelzeile
        feld("topleft",     ox,               oy,      r,             th, titel, "tl")
        feld("top",         ox + r,           oy,      breite - 2*r,  th, titel, "t")
        feld("topright",    ox + breite - r,  oy,      r,             th, titel, "tr")
        # Fensterinhalt - die Mitte bleibt leer, dort liegt das Fenster
        feld("left",        ox,               oy + th, r,             mitte_h, flaeche, "l")
        t.append(f'  <g id="{praefix}-center">')
        t.append(f'    <rect x="{ox + r:g}" y="{oy + th:g}" '
                 f'width="{breite - 2*r:g}" height="{mitte_h:g}" fill="none"/>')
        t.append('  </g>')
        feld("right",       ox + breite - r,  oy + th, r,             mitte_h, flaeche, "r")
        # Unterkante
        feld("bottomleft",  ox,               oy + hoehe - r, r,            r, flaeche, "bl")
        feld("bottom",      ox + r,           oy + hoehe - r, breite - 2*r, r, flaeche, "b")
        feld("bottomright", ox + breite - r,  oy + hoehe - r, r,            r, flaeche, "br")
        return t

    def decoration(self):
        b, h = 200, 120
        luft = 20
        teile = []
        # aktiv
        teile += self._patch("decoration", luft, luft, b, h,
                             self.f("kopf_aktiv"), self.f("flaeche"))
        # inaktiv
        teile += self._patch("decoration-inactive", luft, luft + h + luft, b, h,
                             self.f("kopf_inaktiv"), self.f("flaeche"))

        # Maximiert: nur die Titelleiste, kein Rahmen ringsum.
        for name, farbe, oy in [
            ("decoration-maximized-center", self.f("kopf_aktiv"), luft + 2*(h+luft)),
            ("decoration-maximized-inactive-center", self.f("kopf_inaktiv"),
             luft + 2*(h+luft) + self.th + luft),
        ]:
            teile.append(f'  <g id="{name}">')
            teile.append(f'    <rect x="{luft}" y="{oy}" width="{b}" '
                         f'height="{self.th}" fill="{farbe}"/>')
            teile.append(f'    <rect x="{luft}" y="{oy + self.th - self.aussen}" '
                         f'width="{b}" height="{self.aussen}" fill="{self.f("rahmen")}"/>')
            teile.append('  </g>')

        gh = luft + 2*(h+luft) + 2*(self.th + luft)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{b + 2*luft}" '
                f'height="{gh}" viewBox="0 0 {b + 2*luft} {gh}">\n'
                '  <!-- Erzeugt von tools/gen-aurorae.py.\n'
                '       Die IDs sind der Vertrag mit KWin - nicht umbenennen. -->\n'
                + "\n".join(teile) + '\n</svg>\n')

    def button(self, art):
        """Ein Button je Zustand. Quadratisch mit 3D-Kante, wie NT.

        Das Symbol (X, Kasten, Strich) wird als Pfad in Textfarbe
        darueber gezeichnet.
        """
        g, a, b = self.bg, self.aussen, self.bevel
        luft = 4
        teile = []

        for i, zustand in enumerate(BUTTON_ZUSTAENDE):
            ox = luft + i * (g + luft)
            oy = luft
            gedrueckt = zustand == "pressed"
            grund = self.f("hover") if zustand == "hover" else self.f("flaeche")
            if zustand == "deactivated":
                grund = self.f("dunkel")
            hell = self.f("dunkel" if gedrueckt else "hell")
            dunkel = self.f("hell" if gedrueckt else "dunkel")
            strich = self.f("text")

            teile.append(f'  <g id="{zustand}-center">')
            teile.append(f'    <rect x="{ox}" y="{oy}" width="{g}" height="{g}" fill="{grund}"/>')
            # Aussenrahmen
            teile.append(f'    <rect x="{ox}" y="{oy}" width="{g}" height="{a}" fill="{self.f("rahmen")}"/>')
            teile.append(f'    <rect x="{ox}" y="{oy+g-a}" width="{g}" height="{a}" fill="{self.f("rahmen")}"/>')
            teile.append(f'    <rect x="{ox}" y="{oy}" width="{a}" height="{g}" fill="{self.f("rahmen")}"/>')
            teile.append(f'    <rect x="{ox+g-a}" y="{oy}" width="{a}" height="{g}" fill="{self.f("rahmen")}"/>')
            # 3D-Kante
            teile.append(f'    <rect x="{ox+a}" y="{oy+a}" width="{g-2*a}" height="{b}" fill="{hell}"/>')
            teile.append(f'    <rect x="{ox+a}" y="{oy+a}" width="{b}" height="{g-2*a}" fill="{hell}"/>')
            teile.append(f'    <rect x="{ox+a}" y="{oy+g-a-b}" width="{g-2*a}" height="{b}" fill="{dunkel}"/>')
            teile.append(f'    <rect x="{ox+g-a-b}" y="{oy+a}" width="{b}" height="{g-2*a}" fill="{dunkel}"/>')

            # Symbol, um einen Pixel versetzt wenn gedrueckt
            v = 1 if gedrueckt else 0
            m = ox + g / 2 + v
            n = oy + g / 2 + v
            # Symbolgroesse an der Buttonflaeche ausgerichtet statt
            # fest: bei 18px-Buttons war ein fester Wert von 2.5 zu
            # klein, das X war kaum zu erkennen. 0.72 laesst genug Rand
            # zum 3D-Rahmen.
            s = (g - 2 * (a + b)) * 0.72 / 2
            if art == "close":
                teile.append(f'    <path d="M{m-s},{n-s} L{m+s},{n+s} M{m+s},{n-s} '
                             f'L{m-s},{n+s}" stroke="{strich}" stroke-width="1.5"/>')
            elif art == "maximize":
                teile.append(f'    <rect x="{m-s}" y="{n-s}" width="{2*s}" height="{2*s}" '
                             f'fill="none" stroke="{strich}" stroke-width="1.5"/>')
            elif art == "minimize":
                teile.append(f'    <rect x="{m-s}" y="{n+s-1.5}" width="{2*s}" height="1.5" '
                             f'fill="{strich}"/>')
            elif art == "restore":
                teile.append(f'    <rect x="{m-s}" y="{n-s+1.5}" width="{2*s-1.5}" '
                             f'height="{2*s-1.5}" fill="none" stroke="{strich}" stroke-width="1.2"/>')
                teile.append(f'    <path d="M{m-s+1.5},{n-s+1.5} L{m-s+1.5},{n-s} '
                             f'L{m+s},{n-s} L{m+s},{n+s-1.5}" fill="none" '
                             f'stroke="{strich}" stroke-width="1.2"/>')
            elif art in ("keepabove", "keepbelow", "alldesktops", "shade", "help", "menu"):
                teile.append(f'    <rect x="{m-s}" y="{n-1}" width="{2*s}" height="2" '
                             f'fill="{strich}"/>')
            teile.append('  </g>')

        breite = luft + len(BUTTON_ZUSTAENDE) * (g + luft)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{breite}" '
                f'height="{g + 2*luft}" viewBox="0 0 {breite} {g + 2*luft}">\n'
                + "\n".join(teile) + '\n</svg>\n')

    def rc(self, name):
        def rgb(h):
            h = h.lstrip("#")
            return ",".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
        r = self.rahmen
        return f"""[General]
ActiveTextColor={rgb(self.f("auswahl_text", "fenster"))}
InactiveTextColor={rgb(self.f("fenster"))}
TitleAlignment=Left
TitleVerticalAlignment=Center
UseTextShadow=false
Animation=0
Shadow=true

[Layout]
BorderLeft={r}
BorderRight={r}
BorderBottom={r}
TitleHeight={self.th}
TitleEdgeTop=0
TitleEdgeTopMaximized=0
TitleEdgeBottom=0
TitleEdgeBottomMaximized=0
TitleEdgeLeft={r}
TitleEdgeLeftMaximized=2
TitleEdgeRight={r}
TitleEdgeRightMaximized=2
TitleBorderLeft=4
TitleBorderRight=4
ButtonWidth={self.bg}
ButtonHeight={self.bg}
ButtonSpacing=2
ButtonMarginTop={max(0, (self.th - self.bg) // 2)}
ExplicitButtonSpacer=4
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
"""

    def metadata(self, name, anzeige, beschreibung, autor, lizenz, version):
        # Aurorae nutzt metadata.desktop - hier ist das kein Legacy,
        # sondern das vorgesehene Format. Der Praefix
        # __aurorae__svg__ ist Pflicht und muss dem Ordnernamen folgen.
        return f"""[Desktop Entry]
Name={anzeige}
Comment={beschreibung}
Type=Service
X-KDE-ServiceTypes=KWin/Decoration
X-KDE-Library=kwin3_aurorae
X-KDE-PluginInfo-Name=__aurorae__svg__{name}
X-KDE-PluginInfo-Author={autor}
X-KDE-PluginInfo-License={lizenz}
X-KDE-PluginInfo-Version={version}
"""


PALETTE_NT = {
    "flaeche": "#d8d8d0", "fenster": "#f0f0e8",
    "kopf_aktiv": "#176b78", "kopf_inaktiv": "#60777a",
    "hell": "#f4f4ee", "dunkel": "#8a8a82", "rahmen": "#202628",
    "text": "#202628", "auswahl_text": "#ffffff", "hover": "#d6a23a",
}


def main():
    ap = argparse.ArgumentParser(description="Erzeugt eine Aurorae-Dekoration.")
    ap.add_argument("--name", default="NTLegacy")
    ap.add_argument("--anzeige", default="NT Legacy")
    ap.add_argument("-o", "--ausgabe", type=Path, required=True)
    ap.add_argument("--titelhoehe", type=int, default=22)
    ap.add_argument("--rahmen", type=int, default=4)
    ap.add_argument("--button", type=int, default=14)
    ap.add_argument("--autor", default="huppiflupp")
    ap.add_argument("--lizenz", default="GPL-2.0-or-later")
    ap.add_argument("--version", default="0.1.0")
    args = ap.parse_args()

    a = Aurorae(PALETTE_NT, titelhoehe=args.titelhoehe,
                rahmen=args.rahmen, buttongroesse=args.button)
    ziel = args.ausgabe / args.name
    ziel.mkdir(parents=True, exist_ok=True)

    (ziel / "decoration.svg").write_text(a.decoration())
    print(f"  {ziel.name}/decoration.svg")
    for btn in BUTTONS:
        (ziel / f"{btn}.svg").write_text(a.button(btn))
    print(f"  {ziel.name}/*.svg ({len(BUTTONS)} Buttons)")
    (ziel / f"{args.name}rc").write_text(a.rc(args.name))
    print(f"  {ziel.name}/{args.name}rc")
    (ziel / "metadata.desktop").write_text(a.metadata(
        args.name, args.anzeige,
        "Windows NT 4.0 in Petrol - eckige Rahmen, quadratische Knoepfe",
        args.autor, args.lizenz, args.version))
    print(f"  {ziel.name}/metadata.desktop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
