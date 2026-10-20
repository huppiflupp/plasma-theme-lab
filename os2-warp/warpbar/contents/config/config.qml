import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: i18nd("warp-legacy", "Tray"); icon: "system-run"; source: "configTray.qml" }
    ConfigCategory { name: i18nd("warp-legacy", "Panels"); icon: "preferences-desktop"; source: "PanelsPage.qml" }
}
