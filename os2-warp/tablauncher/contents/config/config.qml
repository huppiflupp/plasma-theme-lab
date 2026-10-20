import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: i18nd("warp-legacy", "Main tab"); icon: "system-run"; source: "configMain.qml" }
    ConfigCategory { name: i18nd("warp-legacy", "Panels"); icon: "preferences-desktop"; source: "PanelsPage.qml" }
}
