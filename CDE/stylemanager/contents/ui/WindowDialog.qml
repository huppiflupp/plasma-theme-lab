import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Window: the frame's short hard shadow (an option of the decoration,
// also in System Settings' window decoration page).
StyleDialog {
    id: dialog
    heading: i18nd("cde-copper", "Window")
    iconName: "preferences-desktop-theme-windowdecorations"
    onLoad: windowShadow.checked = manager.installed.window_shadow !== false
    onApply: if (windowShadow.checked !== (manager.installed.window_shadow !== false))
        manager.apply("--window-shadow " + (windowShadow.checked ? "on" : "off"),
                      windowShadow.checked ? i18nd("cde-copper", "Window shadow on") : i18nd("cde-copper", "Window shadow off"), false)
    CheckBox {
        id: windowShadow
        text: i18nd("cde-copper", "Short hard shadow at the right and bottom of each window")
    }
    Label {
        Layout.fillWidth: true; Layout.maximumWidth: 460
        wrapMode: Text.Wrap; opacity: 0.8
        text: i18nd("cde-copper", "Open windows take it at once.")
    }
}
