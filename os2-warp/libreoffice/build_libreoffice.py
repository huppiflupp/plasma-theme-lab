#!/usr/bin/env python3
"""LibreOffice colours for Warp Legacy (LibreOffice's "Application Colors").

    build_libreoffice(out, variants, version)

writes, from the palettes in ../build.py:

    out/warp-legacy.oxt       a configuration-only extension: two colour
                              schemes, "Warp Legacy" and "Warp Legacy Neon",
                              in Tools › Options › LibreOffice › Application
                              Colors (document, application background,
                              text boundaries, grid, marks, links …)
    out/libreoffice-apply     installs the extension and chooses a scheme
                              (with LibreOffice closed), or takes it back

The window around the document (menus, toolbars, sidebar) is not part of
it: with the kf6/qt6 VCL plugin LibreOffice draws it with the Kvantum style
Warp/WarpNeon and the Plasma colour scheme already. The schemes leave
LibreOffice's own UI colours (WindowColor, MenuColor …) automatic, so the
two never fight.

Run alone (python3 libreoffice/build_libreoffice.py) it builds into
build/warp-legacy/libreoffice, which install.sh copies to
~/.local/share/warp-legacy/libreoffice.
"""
import importlib.util
import shutil
import stat
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
EXTENSION_ID = "org.warplegacy.libreoffice"
# The scheme names are the names LibreOffice lists; libreoffice-apply knows
# them as well.
SCHEME = {"": "Warp Legacy", "neon": "Warp Legacy Neon"}


def roles(P, neon):
    """Colour per ColorScheme entry (officecfg UI.xcs, LibreOffice 26.2).
    Entries not named here stay automatic."""
    if neon:
        cyan, violet, pink = P["light"], P["dark"], P["selection_glow"][2]
        return dict(
            # The page a step lighter than the workspace round it, as the
            # windows on the Neon desktop; automatic text turns light on it.
            DocColor=P["surface"], AppBackground=P["border"], FontColor=P["text"],
            # Text and table boundaries as the edges of every Neon control.
            DocBoundaries=violet, TableBoundaries="#3a4a78",
            Links=P["link"], LinksVisited=P["visited"],
            Spell=pink, Grammar=cyan, SmartTags=P["visited"],
            Shadow=P["border"],
            WriterTextGrid="#3a4a78", WriterFieldShadings=P["hover"], WriterIdxShadings=P["hover"],
            WriterDirectCursor=P["text"], WriterSectionBoundaries=violet,
            WriterHeaderFooterMark=cyan, WriterPageBreaks=violet, WriterNonPrintChars=cyan,
            HTMLSGML=cyan, HTMLComment=P["positive"], HTMLKeyword=pink, HTMLUnknown=P["warning"],
            CalcGrid="#26346e", CalcCellFocus=P["selection"],
            CalcPageBreak=violet, CalcPageBreakManual=pink, CalcPageBreakAutomatic=violet,
            CalcHiddenColRow=violet, CalcTextOverflow=pink, CalcComments=P["warning"],
            CalcDetective=cyan, CalcDetectiveError=P["error"], CalcReference=pink,
            CalcNotesBackground=P["hover"], CalcValue=P["link"], CalcFormula=P["positive"],
            CalcText=P["text"], CalcProtectedBackground=P["panel"],
            DrawGrid="#3a4a78",
            Author1=cyan, Author2=pink, Author3=P["visited"], Author4=P["positive"],
            Author5=P["warning"], Author6="#7aa6ff", Author7=P["error"], Author8="#9fe9ff",
            Author9="#ffd08a",
            BASICEditor=P["window"], BASICIdentifier=P["text"], BASICComment="#7f8fbf",
            BASICNumber=P["warning"], BASICString=P["positive"], BASICOperator=cyan,
            BASICKeyword=pink, BASICError=P["error"],
            SQLIdentifier=P["text"], SQLNumber=P["warning"], SQLString=P["positive"],
            SQLOperator=cyan, SQLKeyword=pink, SQLParameter=P["visited"], SQLComment="#7f8fbf",
        )
    # Classic Warp 4: white page on the grey workspace, Warp blue for what
    # is marked, OS/2's VGA colours for the rest.
    return dict(
        DocColor=P["window"], AppBackground=P["dark"], FontColor=P["text"],
        DocBoundaries=P["dark"], TableBoundaries=P["dark"],
        Links=P["link"], LinksVisited=P["visited"],
        Spell=P["error"], Grammar=P["link"], SmartTags=P["visited"],
        Shadow=P["text2"],
        WriterFieldShadings="#cccccc", WriterIdxShadings="#cccccc",
        WriterSectionBoundaries=P["dark"], WriterHeaderFooterMark=P["link"],
        WriterPageBreaks=P["link"], WriterNonPrintChars=P["link"],
        CalcGrid="#c0c0c0", CalcCellFocus=P["selection"],
        CalcPageBreak=P["link"], CalcPageBreakManual=P["link"], CalcPageBreakAutomatic=P["dark"],
        CalcHiddenColRow=P["link"], CalcTextOverflow=P["error"],
        CalcDetective=P["link"], CalcDetectiveError=P["error"], CalcReference=P["error"],
        CalcNotesBackground="#ffffc0", CalcValue=P["link"], CalcFormula=P["positive"],
        CalcText=P["text"], CalcProtectedBackground="#cccccc",
        DrawGrid=P["dark"],
        Author1=P["selection"], Author2=P["error"], Author3=P["positive"], Author4=P["visited"],
        Author5=P["warning"], Author6="#00a0a0",
    )


def scheme_xml(name, colours):
    nodes = []
    for entry, value in colours.items():
        props = f'<prop oor:name="Color"><value>{int(value[1:7], 16)}</value></prop>'
        # Links are only coloured with IsVisible (the box in the dialog).
        if entry in ("Links", "LinksVisited"):
            props = '<prop oor:name="IsVisible"><value>true</value></prop>' + props
        nodes.append(f'      <node oor:name="{entry}">{props}</node>')
    return (f'    <node oor:name="{escape(name)}" oor:op="replace">\n'
            + "\n".join(nodes) + "\n    </node>\n")


def build_libreoffice(out, variants, version):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    schemes = "".join(scheme_xml(SCHEME[v["key"]], roles(v["P"], v["key"] == "neon")) for v in variants)
    files = {
        "META-INF/manifest.xml": """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="http://openoffice.org/2001/manifest">
  <manifest:file-entry manifest:full-path="ColorScheme.xcu" manifest:media-type="application/vnd.sun.star.configuration-data"/>
</manifest:manifest>
""",
        "description.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<description xmlns="http://openoffice.org/extensions/description/2006"
             xmlns:xlink="http://www.w3.org/1999/xlink">
  <identifier value="{EXTENSION_ID}"/>
  <version value="{version}"/>
  <display-name>
    <name lang="en">Warp Legacy colours</name>
    <name lang="de">Warp-Legacy-Farben</name>
  </display-name>
  <publisher>
    <name xlink:href="https://github.com/huppiflupp/plasma-theme-lab" lang="en">Warp Legacy contributors</name>
  </publisher>
  <extension-description>
    <src lang="en" xlink:href="description-en.txt"/>
    <src lang="de" xlink:href="description-de.txt"/>
  </extension-description>
</description>
""",
        "description-en.txt": "Application colours after OS/2 Warp 4: \"Warp Legacy\" (grey and white, "
                              "Warp blue) and \"Warp Legacy Neon\" (navy, cyan, violet, pink). Choose them "
                              "in Tools > Options > LibreOffice > Application Colors. GPL-2.0-or-later.\n",
        "description-de.txt": "Anwendungsfarben nach OS/2 Warp 4: „Warp Legacy“ (grau und weiß, Warp-Blau) "
                              "und „Warp Legacy Neon“ (Navy, Cyan, Violett, Pink). Auswahl unter Extras > "
                              "Optionen > LibreOffice > Anwendungsfarben. GPL-2.0-or-later.\n",
        "ColorScheme.xcu": f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Warp Legacy {version}: generated by libreoffice/build_libreoffice.py from build.py's palettes -->
<oor:component-data xmlns:oor="http://openoffice.org/2001/registry"
                    xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    oor:name="UI" oor:package="org.openoffice.Office">
 <node oor:name="ColorScheme">
  <node oor:name="ColorSchemes">
{schemes}  </node>
 </node>
</oor:component-data>
""",
    }
    # Fixed dates: the same palettes give the same file.
    with zipfile.ZipFile(out / "warp-legacy.oxt", "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, text)
    apply = out / "libreoffice-apply"
    shutil.copy2(HERE / "libreoffice-apply", apply)
    apply.chmod(apply.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


if __name__ == "__main__":
    root = HERE.parent
    spec = importlib.util.spec_from_file_location("warp_build", root / "build.py")
    build = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root))
    spec.loader.exec_module(build)
    target = build.OUT / "warp-legacy/libreoffice"
    build_libreoffice(target, build.VARIANTS, build.VERSION)
    print(f"LibreOffice colours built in {target}")
