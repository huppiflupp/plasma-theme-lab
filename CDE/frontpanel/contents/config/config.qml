import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: i18nd("cde-copper", "Front Console"); icon: "preferences-system"; source: "configGeneral.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Style"); icon: "preferences-desktop-color"; source: "configStyle.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Launchers"); icon: "system-run"; source: "configLaunchers.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Workspaces"); icon: "virtual-desktops"; source: "configWorkspaces.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Clock and Calendar"); icon: "view-calendar"; source: "configCalendar.qml" }
}
