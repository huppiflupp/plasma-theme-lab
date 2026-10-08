import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Screen: which lock screen, CDE's or Plasma's.
StyleDialog {
    id: dialog
    heading: i18ndc("cde-copper", "style manager part", "Lock Screen")
    iconName: "system-lock-screen"
    onLoad: (manager.installed.lockscreen === "plasma" ? plasma : cde).checked = true
    onApply: {
        const kind = plasma.checked ? "plasma" : "cde";
        if (kind !== (manager.installed.lockscreen || "cde"))
            manager.apply("--lockscreen " + kind, i18nd("cde-copper", "Lock screen: %1", plasma.checked ? plasma.text : cde.text), false);
    }
    RadioButton { id: cde; text: i18nd("cde-copper", "CDE's: a Motif dialog on the backdrop") }
    RadioButton { id: plasma; text: i18nd("cde-copper", "Plasma's own") }
    Label {
        Layout.fillWidth: true; Layout.maximumWidth: 460
        wrapMode: Text.Wrap; opacity: 0.8
        text: i18nd("cde-copper", "Plasma takes the lock screen from its shell package; CDE's comes in a shell package of its own that takes everything else from Plasma's. Switching restarts the desktop shell once.")
    }
}
