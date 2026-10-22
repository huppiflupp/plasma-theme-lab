"""CDE Copper: re-applies the theme's colours after a palette change.

FreeCAD copies a preference pack's values only when the pack is chosen. CDE
Copper rewrites its pack whenever the palette changes; while the CDE Copper
theme is chosen, this copies the newer colours at start-up (and stores the
pack's stamp, so it does so once). Written by CDE Copper; it removes it again.
"""
import FreeCAD


# FreeCAD runs this file with separate globals and locals: names defined at
# the top would be invisible inside a function, so everything stays in it.
def _apply():
    import os
    import xml.etree.ElementTree as ET
    NAME = "CDE Copper"
    folder = os.path.join(FreeCAD.getUserAppDataDir(), "SavedPreferencePacks", NAME)
    path = os.path.join(folder, NAME + ".cfg")
    main = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
    if main.GetString("Theme") != NAME or not os.path.isfile(path):
        return
    stamp = str(os.path.getmtime(path))
    own = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/CDECopper")
    if own.GetString("Applied") == stamp:
        return

    pending = [(ET.parse(path).getroot().find("FCParamGroup"), "")]
    while pending:
        element, prefix = pending.pop()
        for child in element:
            name = child.get("Name")
            if child.tag == "FCParamGroup":
                pending.append((child, prefix + "/" + name if prefix else name))
                continue
            group = FreeCAD.ParamGet("User parameter:" + prefix)
            if child.tag == "FCUInt":
                group.SetUnsigned(name, int(child.get("Value")))
            elif child.tag == "FCBool":
                group.SetBool(name, child.get("Value") == "1")
            elif child.tag == "FCText":
                group.SetString(name, child.text or "")
    own.SetString("Applied", stamp)


try:
    _apply()
except Exception as error:
    FreeCAD.Console.PrintWarning("CDE Copper: " + str(error) + "\n")
