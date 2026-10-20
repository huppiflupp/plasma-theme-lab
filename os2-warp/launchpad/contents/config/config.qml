import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory { name: i18nd("warp-legacy", "Launchers"); icon: "system-run"; source: "configLaunchers.qml" }
    ConfigCategory { name: i18nd("warp-legacy", "Panels"); icon: "preferences-desktop"; source: "PanelsPage.qml" }
}
