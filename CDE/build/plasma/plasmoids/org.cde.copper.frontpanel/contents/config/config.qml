import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    // By the questions one comes with: the console itself, what it holds,
    // the windows, the clock. (The desktop's style is the Style Manager's.)
    ConfigCategory { name: i18nd("cde-copper", "Console"); icon: "preferences-system"; source: "configGeneral.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Tiles"); icon: "system-run"; source: "configLaunchers.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Windows and Workspaces"); icon: "virtual-desktops"; source: "configWorkspaces.qml" }
    ConfigCategory { name: i18nd("cde-copper", "Clock and Calendar"); icon: "view-calendar"; source: "configCalendar.qml" }
}
