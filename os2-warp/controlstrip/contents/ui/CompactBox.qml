pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import "feeds.js" as Feeds

// The Control Strip as the box of the user's Neon concept
// (reference/neon-2026.png, top right): a mark, the time and date, CPU,
// memory and disk with thin bars, a curve of the processor's last minute,
// a motto. Our mark is "Warp Legacy"; the concept's OS/2 word mark is
// IBM's (DESIGN.md §1).
//
// Made useful (IDEEN.md): the top shows the next appointments (the mark
// when there are none) or the weather, the bottom a rotating saying or news
// headlines; the clock opens the calendar, the meters the system monitor,
// "/" the disk usage. Top and bottom keep a fixed height, so the floating
// panel does not jump when their text changes.
//
// No frame of its own: the panel's background is the frame. Drawn as a
// Bevel the box had a second frame inside the panel's (the user's remark,
// compared with the concept, 21.10.2026).
Item {
    id: box
    required property var root
    implicitHeight: column.implicitHeight + 16
    readonly property bool neon: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
    readonly property color dark: neon ? Kirigami.Theme.hoverColor : "#808080"
    readonly property color bright: box.neon ? "#cfeeff" : Kirigami.Theme.textColor
    readonly property color cyan: box.neon ? "#3ad0ff" : Kirigami.Theme.linkColor
    readonly property color lavender: box.neon ? "#e2b8ff" : Kirigami.Theme.highlightColor

    // A thin line of light between the parts: cyan into pink, fading out.
    component Divider: Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.1) }
            GradientStop { position: 0.4; color: box.cyan }
            GradientStop { position: 0.8; color: box.neon ? "#ff4fd8" : box.dark }
            GradientStop { position: 1.0; color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.1) }
        }
    }
    // A clickable part: a faint glow under the pointer, a tooltip.
    component Spot: MouseArea {
        id: spot
        property string tip
        anchors.fill: parent
        anchors.margins: -3
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        Rectangle {
            anchors.fill: parent
            radius: 3
            color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, spot.containsMouse ? 0.12 : 0)
        }
        PlasmaCore.ToolTipArea { anchors.fill: parent; mainText: spot.tip; active: spot.tip !== "" }
    }
    // A reading: name, percent, a thin bar.
    component Meter: RowLayout {
        id: meter
        property string name
        property real part
        spacing: 6
        Text { text: meter.name; color: box.cyan; font.pixelSize: 13; Layout.preferredWidth: 32 }
        Text {
            text: Math.round(meter.part * 100) + "%"
            color: box.cyan; font.pixelSize: 13
            horizontalAlignment: Text.AlignRight
            Layout.preferredWidth: 36
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.35)
            Rectangle {
                x: 1; y: 1; height: parent.height - 2
                width: Math.max(0, (parent.width - 2) * Math.min(1, meter.part))
                color: box.cyan
            }
        }
    }

    ColumnLayout {
        id: column
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
        spacing: 6

        // The top: appointments, the weather, or the mark.
        Item {
            id: header
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            readonly property string mode: box.root.topPart === "events" && box.root.upcoming.length ? "events"
                                           : box.root.topPart === "weather" && box.root.weather ? "weather" : "mark"
            Spot {
                visible: box.root.topPart !== "mark"
                tip: box.root.topPart === "weather"
                     ? (box.root.weather ? box.root.tr("%1 – open the forecast", box.root.weather.place || box.root.weather.text)
                                         : box.root.tr("No weather data yet"))
                     : box.root.tr("Calendar")
                onClicked: box.root.topPart === "weather"
                           ? box.root.open(Feeds.weatherPage(box.root.cfg.weatherServer, box.root.cfg.weatherPlace, box.root.lang))
                           : box.root.openCalendar(box)
            }

            // The mark: a globe behind "Warp" and the year.
            Item {
                anchors.fill: parent
                visible: header.mode === "mark"
                Kirigami.Icon {
                    anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    width: 50; height: 50
                    source: "internet-web-browser"
                    opacity: 0.85
                }
                Text {
                    id: word
                    y: 2
                    text: "WARP"
                    font.family: Kirigami.Theme.defaultFont.family
                    font.pixelSize: 28; font.bold: true; font.italic: true
                    color: box.cyan
                    style: box.neon ? Text.Outline : Text.Normal
                    styleColor: Qt.rgba(0.16, 0.36, 1, 0.45)
                }
                // "Legacy" in a bold italic Times, as the user asked; fontconfig
                // gives the metric twin (Liberation Serif) where Times New
                // Roman is not installed, which is the free one we rely on.
                Text {
                    anchors.top: word.bottom; anchors.topMargin: -8
                    x: 18
                    text: "Legacy"
                    font.family: "Times New Roman"
                    font.pixelSize: 24; font.bold: true; font.italic: true
                    color: box.lavender
                }
            }

            // The next two appointments: when, then what.
            Column {
                anchors.fill: parent
                visible: header.mode === "events"
                spacing: 0
                Repeater {
                    model: box.root.upcoming
                    Column {
                        id: event
                        required property var modelData
                        width: parent.width
                        Text {
                            width: parent.width
                            text: box.root.dayLabel(event.modelData)
                            color: box.cyan; font.pixelSize: 11
                            elide: Text.ElideRight
                        }
                        Text {
                            width: parent.width
                            text: event.modelData.title
                            color: box.bright; font.pixelSize: 13
                            elide: Text.ElideRight
                        }
                    }
                }
            }

            // The weather: its icon, the temperature, the sky in words.
            Item {
                anchors.fill: parent
                visible: header.mode === "weather"
                Kirigami.Icon {
                    id: sky
                    anchors.verticalCenter: parent.verticalCenter
                    width: 44; height: 44
                    source: box.root.weather ? box.root.weather.icon : ""
                }
                Text {
                    anchors.left: sky.right; anchors.leftMargin: 8
                    anchors.right: parent.right
                    y: 4
                    text: box.root.weather ? box.root.weather.temp : ""
                    color: box.bright; font.pixelSize: 24; font.weight: Font.Light
                }
                Text {
                    anchors.left: sky.right; anchors.leftMargin: 8
                    anchors.right: parent.right
                    y: 34
                    text: box.root.weather ? box.root.weather.text : ""
                    color: box.cyan; font.pixelSize: 11
                    elide: Text.ElideRight
                }
                Text {
                    anchors.left: sky.right; anchors.leftMargin: 8
                    anchors.right: parent.right
                    y: 48
                    text: box.root.weather ? box.root.weather.place : ""
                    color: box.lavender; font.pixelSize: 10
                    elide: Text.ElideRight
                }
            }
        }
        Divider {}
        // Time and date: a click opens the calendar. (The click areas sit
        // beside the layouts, not in them: a layout places its children.)
        Item {
            id: clock
            Layout.fillWidth: true
            Layout.preferredHeight: clockColumn.implicitHeight
            ColumnLayout {
                id: clockColumn
                width: parent.width
                spacing: 0
                Text {
                    text: Qt.formatTime(box.root.now, "hh:mm")
                    color: box.bright
                    font.pixelSize: 30; font.weight: Font.Light
                }
                Text {
                    text: Qt.formatDate(box.root.now, "dd.MM.yyyy")
                    color: box.cyan; font.pixelSize: 15
                }
                Text {
                    text: Qt.locale().toString(box.root.now, "ddd, d. MMM")
                    color: box.cyan; font.pixelSize: 11; opacity: 0.85
                }
            }
            Spot { tip: box.root.tr("Calendar"); onClicked: box.root.openCalendar(box) }
        }
        Divider {}
        // Processor and memory: a click opens the system monitor.
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: meters.implicitHeight
            ColumnLayout {
                id: meters
                width: parent.width
                spacing: 6
                Meter { Layout.fillWidth: true; name: "CPU"; part: box.root.cpu }
                Meter { Layout.fillWidth: true; name: "RAM"; part: box.root.memoryPart }
            }
            Spot { tip: box.root.tr("System monitor"); onClicked: box.root.launch("@sysmon") }
        }
        // The root file system: a click shows what fills it.
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: rootMeter.implicitHeight
            Meter { id: rootMeter; width: parent.width; name: "/"; part: box.root.rootPart }
            Spot { tip: box.root.tr("Disk usage"); onClicked: box.root.launch("@diskusage") }
        }
        // The processor's last minute.
        Canvas {
            id: curve
            Layout.fillWidth: true
            Layout.preferredHeight: 26
            readonly property var points: box.root.cpuHistory
            onPointsChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = Qt.rgba(box.cyan.r, box.cyan.g, box.cyan.b, 0.35).toString();
                ctx.beginPath(); ctx.moveTo(0, height - 0.5); ctx.lineTo(width, height - 0.5); ctx.stroke();
                const n = points.length;
                if (n < 2) return;
                ctx.strokeStyle = box.cyan.toString();
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                for (let i = 0; i < n; i++) {
                    const x = width * i / 29, y = height - 2 - (height - 4) * points[i];
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }
                ctx.stroke();
            }
            Spot { tip: box.root.tr("System monitor"); onClicked: box.root.launch("@sysmon") }
        }

        // The bottom: the fixed motto as before ...
        Text {
            visible: box.root.bottomPart === "motto" && text !== ""
            Layout.fillWidth: true
            Layout.topMargin: 4
            text: box.root.tr(box.root.cfg.motto)
            color: box.cyan
            font.pixelSize: 14; font.italic: true
            wrapMode: Text.WordWrap
        }
        // ... a saying (a click shows the next) or a headline (a click
        // opens the article), in a fixed height: long ones shrink to fit.
        Item {
            id: footer
            visible: box.root.bottomPart === "sayings" || box.root.bottomPart === "news"
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.preferredHeight: 76
            readonly property var item: box.root.news ? box.root.news.items[(Math.floor(box.root.now.getTime() / 60000)) % box.root.news.items.length] : null
            readonly property bool news: box.root.bottomPart === "news"
            Spot {
                tip: footer.news ? (footer.item ? (box.root.news.source || box.root.tr("Open the article")) : "")
                                 : box.root.tr("Next saying")
                cursorShape: footer.news && !(footer.item && footer.item.link) ? Qt.ArrowCursor : Qt.PointingHandCursor
                onClicked: footer.news ? (footer.item && box.root.open(footer.item.link)) : box.root.sayingStep++
            }
            Text {
                id: line
                anchors { left: parent.left; right: parent.right; top: parent.top }
                height: 62
                text: footer.news ? (footer.item ? footer.item.title : box.root.tr("No headlines yet")) : box.root.saying.text
                color: box.cyan
                opacity: footer.news && !footer.item ? 0.6 : 1
                font.pixelSize: 13; font.italic: !footer.news
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                maximumLineCount: 4
                fontSizeMode: Text.VerticalFit
                minimumPixelSize: 10
                verticalAlignment: Text.AlignTop
            }
            Text {
                anchors { left: parent.left; right: parent.right }
                y: Math.min(line.height, line.contentHeight) + 3
                text: footer.news ? (box.root.news ? box.root.news.source : "") : "— " + box.root.saying.by
                horizontalAlignment: footer.news ? Text.AlignLeft : Text.AlignRight
                color: box.lavender
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }
    }
}
