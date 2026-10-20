import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: i18nd("warp-legacy", "Control Strip"); icon: "computer"; source: "configStrip.qml" }
    ConfigCategory { name: i18nd("warp-legacy", "Panels"); icon: "preferences-desktop"; source: "PanelsPage.qml" }
}
