pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import "launch.js" as Launch

// Settings page. Plasma hands every page every setting's default, declared
// here so it takes them quietly; the settings themselves only where shown:
// Plasma saves every cfg_ property a page has, and an unshown one would
// write back a stale value (found in CDE Copper, ConfigPage.qml).
KCM.SimpleKCM {
    id: page
    property var cfg_launchersDefault
    property var cfg_textButtonsDefault
    property var cfg_trayDefault
    property var cfg_mainDefault
    property var cfg_currentTabDefault
    property var cfg_showWorkspacesDefault
    property var cfg_showGaugesDefault
    property var cfg_showClockDefault
    property var cfg_layoutDefault
    property var cfg_mottoDefault
    property var cfg_collapsedDefault
    property var cfg_drawerWidthDefault
    property var cfg_thisWorkspaceDefault
    property var cfg_startLabelDefault
    property var cfg_compactTopDefault
    property var cfg_compactBottomDefault
    property var cfg_sayingMinutesDefault
    property var cfg_clockOpensAppDefault
    property var cfg_calendarCommandDefault
    property var cfg_enabledCalendarPluginsDefault
    property var cfg_weatherServerDefault
    property var cfg_weatherPlaceDefault
    property var cfg_newsUrlDefault
    property var cfg_fetchMinutesDefault
    property string cfg_launchers
    property bool cfg_showWorkspaces
    property bool cfg_showGauges
    property bool cfg_showClock
    property string cfg_layout
    property string cfg_motto
    property string cfg_compactTop
    property string cfg_compactBottom
    property int cfg_sayingMinutes
    property bool cfg_clockOpensApp
    property string cfg_calendarCommand
    property var cfg_enabledCalendarPlugins: []
    property string cfg_weatherServer
    property string cfg_weatherPlace
    property string cfg_newsUrl
    property int cfg_fetchMinutes
    readonly property bool compact: cfg_layout === "compact"
    readonly property bool online: compact && (cfg_compactTop === "weather" || cfg_compactBottom === "news")

    // A choice of {text, value}, bound to one setting.
    component Choice: ComboBox {
        id: choice
        property string value
        signal chosen(string value)
        textRole: "text"
        currentIndex: Math.max(0, (model || []).findIndex(m => m.value === choice.value))
        onActivated: index => chosen(model[index].value)
    }
    PlasmaCalendar.EventPluginsManager {
        id: calendarPlugins
        Component.onCompleted: populateEnabledPluginsList(page.cfg_enabledCalendarPlugins)
    }
    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        Kirigami.Heading { level: 3; text: i18nd("warp-legacy", "Layout") }
        RadioButton { text: i18nd("warp-legacy", "Strip down the right edge (Object Desktop)"); checked: page.cfg_layout !== "compact"; onToggled: if (checked) page.cfg_layout = "strip" }
        RadioButton { text: i18nd("warp-legacy", "Compact box at the top right (Neon concept)"); checked: page.cfg_layout === "compact"; onToggled: if (checked) page.cfg_layout = "compact" }
        // The compact box (IDEEN.md): what its top and bottom show, what
        // the clock opens; weather and news only fetch once chosen here.
        GridLayout {
            visible: page.compact
            Layout.leftMargin: Kirigami.Units.gridUnit
            columns: 2
            columnSpacing: Kirigami.Units.largeSpacing
            Label { text: i18nd("warp-legacy", "Top:"); Layout.alignment: Qt.AlignRight }
            Choice {
                Layout.fillWidth: true
                value: page.cfg_compactTop
                model: [{text: i18nd("warp-legacy", "Next appointments (the mark when there are none)"), value: "events"},
                        {text: i18nd("warp-legacy", "The Warp Legacy mark"), value: "mark"},
                        {text: i18nd("warp-legacy", "Weather (from the internet)"), value: "weather"}]
                onChosen: value => page.cfg_compactTop = value
            }
            Label { visible: page.cfg_compactTop === "weather"; text: i18nd("warp-legacy", "Place:"); Layout.alignment: Qt.AlignRight }
            TextField {
                visible: page.cfg_compactTop === "weather"
                Layout.fillWidth: true
                text: page.cfg_weatherPlace
                placeholderText: i18nd("warp-legacy", "e.g. Hamburg (empty: guessed from your IP address)")
                onEditingFinished: page.cfg_weatherPlace = text.trim()
            }
            Label { visible: page.cfg_compactTop === "weather"; text: i18nd("warp-legacy", "Weather service:"); Layout.alignment: Qt.AlignRight }
            TextField {
                visible: page.cfg_compactTop === "weather"
                Layout.fillWidth: true
                text: page.cfg_weatherServer
                placeholderText: "https://wttr.in"
                onEditingFinished: page.cfg_weatherServer = text.trim() || "https://wttr.in"
            }
            Label { text: i18nd("warp-legacy", "Clicking the clock:"); Layout.alignment: Qt.AlignRight }
            Choice {
                Layout.fillWidth: true
                value: page.cfg_clockOpensApp ? "app" : "month"
                model: [{text: i18nd("warp-legacy", "Shows the month and its events"), value: "month"},
                        {text: i18nd("warp-legacy", "Opens the calendar application"), value: "app"}]
                onChosen: value => page.cfg_clockOpensApp = value === "app"
            }
            Label { text: i18nd("warp-legacy", "Calendar application:"); Layout.alignment: Qt.AlignRight }
            TextField {
                Layout.fillWidth: true
                text: page.cfg_calendarCommand
                placeholderText: "@calendar"
                onEditingFinished: page.cfg_calendarCommand = text.trim() || "@calendar"
            }
            Label { text: i18nd("warp-legacy", "Events from:"); Layout.alignment: Qt.AlignRight | Qt.AlignTop }
            ColumnLayout {
                spacing: 0
                Repeater {
                    model: calendarPlugins.model
                    delegate: CheckBox {
                        // Roles through model.*: "display" would clash with
                        // AbstractButton.display (CDE Copper's configCalendar.qml).
                        required property var model
                        readonly property string pluginId: model.pluginId
                        text: model.display
                        checked: page.cfg_enabledCalendarPlugins.indexOf(pluginId) >= 0
                        onToggled: {
                            const list = page.cfg_enabledCalendarPlugins.filter(id => id !== pluginId);
                            if (checked) list.push(pluginId);
                            page.cfg_enabledCalendarPlugins = list;
                        }
                    }
                }
                Label {
                    text: i18nd("warp-legacy", "Appointments come from KOrganizer/Akonadi (\"PIM Events\").")
                    opacity: 0.7; font: Kirigami.Theme.smallFont
                }
            }
            Label { text: i18nd("warp-legacy", "Bottom:"); Layout.alignment: Qt.AlignRight }
            Choice {
                Layout.fillWidth: true
                value: page.cfg_compactBottom
                model: [{text: i18nd("warp-legacy", "Sayings (Laozi, Seneca, Marcus Aurelius …)"), value: "sayings"},
                        {text: i18nd("warp-legacy", "A fixed text"), value: "motto"},
                        {text: i18nd("warp-legacy", "News headlines (from the internet)"), value: "news"},
                        {text: i18nd("warp-legacy", "Nothing"), value: "none"}]
                onChosen: value => page.cfg_compactBottom = value
            }
            Label { visible: page.cfg_compactBottom === "sayings"; text: i18nd("warp-legacy", "New saying:"); Layout.alignment: Qt.AlignRight }
            Choice {
                visible: page.cfg_compactBottom === "sayings"
                Layout.fillWidth: true
                value: String(page.cfg_sayingMinutes)
                model: [{text: i18nd("warp-legacy", "Every 15 minutes"), value: "15"},
                        {text: i18nd("warp-legacy", "Every hour"), value: "60"},
                        {text: i18nd("warp-legacy", "Every day"), value: "1440"}]
                onChosen: value => page.cfg_sayingMinutes = Number(value)
            }
            Label { visible: page.cfg_compactBottom === "motto"; text: i18nd("warp-legacy", "Text:"); Layout.alignment: Qt.AlignRight | Qt.AlignTop }
            TextArea {
                visible: page.cfg_compactBottom === "motto"
                Layout.fillWidth: true
                text: page.cfg_motto
                placeholderText: i18nd("warp-legacy", "Motto under the box (empty: none)")
                onEditingFinished: page.cfg_motto = text
            }
            Label { visible: page.cfg_compactBottom === "news"; text: i18nd("warp-legacy", "Feed address:"); Layout.alignment: Qt.AlignRight }
            TextField {
                visible: page.cfg_compactBottom === "news"
                Layout.fillWidth: true
                text: page.cfg_newsUrl
                placeholderText: i18nd("warp-legacy", "https://… (an RSS or Atom feed)")
                onEditingFinished: page.cfg_newsUrl = text.trim()
            }
            Label { visible: page.online; text: i18nd("warp-legacy", "Fetch every:"); Layout.alignment: Qt.AlignRight }
            SpinBox {
                visible: page.online
                from: 15; to: 1440; stepSize: 15
                value: page.cfg_fetchMinutes
                textFromValue: (v, locale) => i18nd("warp-legacy", "%1 min", v)
                valueFromText: (text, locale) => parseInt(text) || 30
                onValueModified: page.cfg_fetchMinutes = value
            }
            Item { visible: page.online; Layout.preferredWidth: 1 }
            Label {
                visible: page.online
                Layout.fillWidth: true
                Layout.preferredWidth: Kirigami.Units.gridUnit * 22
                wrapMode: Text.WordWrap
                opacity: 0.7; font: Kirigami.Theme.smallFont
                text: i18nd("warp-legacy", "Weather and news are fetched from the internet. The services you name see your IP address; nothing else is sent. Without a connection the box stays quiet.")
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        Label { text: i18nd("warp-legacy", "In the strip:"); visible: page.cfg_layout !== "compact" }
        CheckBox { text: i18nd("warp-legacy", "Workspaces in miniature"); checked: page.cfg_showWorkspaces; onToggled: page.cfg_showWorkspaces = checked }
        CheckBox { text: i18nd("warp-legacy", "Swap and disk gauges"); checked: page.cfg_showGauges; onToggled: page.cfg_showGauges = checked }
        CheckBox { text: i18nd("warp-legacy", "Digital clock"); checked: page.cfg_showClock; onToggled: page.cfg_showClock = checked }
        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.Heading { level: 3; text: i18nd("warp-legacy", "Launch list") }
        LauncherEditor {
            Layout.fillWidth: true
            entries: Launch.parse(page.cfg_launchers, Launch.STRIP)
            onEdited: list => page.cfg_launchers = Launch.serialize(list)
        }
        Button { text: i18nd("warp-legacy", "Restore the default launchers"); icon.name: "edit-undo"; onClicked: page.cfg_launchers = "" }
    }
}
