import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: "Front Console"; icon: "preferences-system"; source: "configGeneral.qml" }
    ConfigCategory { name: "Style"; icon: "preferences-desktop-color"; source: "configStyle.qml" }
    ConfigCategory { name: "Launchers"; icon: "system-run"; source: "configLaunchers.qml" }
    ConfigCategory { name: "Clock and Calendar"; icon: "view-calendar"; source: "configCalendar.qml" }
}
