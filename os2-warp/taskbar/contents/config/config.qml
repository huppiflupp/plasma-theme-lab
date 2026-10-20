import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: i18nd("warp-legacy", "Taskbar"); icon: "preferences-system-windows"; source: "configTaskbar.qml" }
    ConfigCategory { name: i18nd("warp-legacy", "Panels"); icon: "preferences-desktop"; source: "PanelsPage.qml" }
}
