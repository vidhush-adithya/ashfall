// ASHFALL — Hub (Super+Alt+S): theme, window style, gaps, corners, performance, mascot.
// Every change applies immediately through `ashfall-set`. Esc closes. Runs only while open.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root
    property var st: ({})
    property var pal: st.palette || ({})
    property var cfg: st.settings || ({})
    readonly property string mono: "JetBrainsMono Nerd Font"
    function c(k, d) { return pal[k] !== undefined ? pal[k] : d }

    Process {
        id: loader
        running: true
        command: ["ashfall-state"]
        stdout: StdioCollector { onStreamFinished: { try { root.st = JSON.parse(text) } catch (e) {} } }
    }
    Process {
        id: setter
        onExited: { loader.running = false; loader.running = true }   // refresh after each change
    }
    function apply(args) {
        if (setter.running) return
        setter.command = ["ashfall-set"].concat(args)
        setter.running = true
    }

    component Label: Text { color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; letterSpacing: 3 } }
    component Pill: Rectangle {
        id: pill
        property string text
        property bool on: false
        signal picked()
        implicitHeight: 32; implicitWidth: t.implicitWidth + 28; radius: 16
        color: on ? root.c("line", "#2a2620") : (hov.containsMouse ? root.c("panel", "#14120f") : "transparent")
        border.width: 1; border.color: on ? root.c("fg", "#a89f8c") : root.c("line2", "#3a352c")
        Text { id: t; anchors.centerIn: parent; text: pill.text; color: pill.on ? root.c("hi", "#c2b8a3") : root.c("dim", "#6e6657")
               font { family: root.mono; pixelSize: 10; letterSpacing: 1; bold: pill.on } }
        MouseArea { id: hov; anchors.fill: parent; hoverEnabled: true; onClicked: pill.picked() }
    }
    component Box: Rectangle {
        default property alias content: inner.data
        Layout.fillWidth: true; implicitHeight: inner.implicitHeight + 28
        radius: 10; color: "transparent"; border.width: 1; border.color: root.c("line", "#2a2620")
        ColumnLayout { id: inner; anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 } spacing: 12 }
    }
    component Stepper: RowLayout {
        id: stp
        property string label
        property string key
        property int value
        property int lo: 0
        property int hi: 16
        property int step: 2
        Layout.fillWidth: true
        Label { text: stp.label; Layout.preferredWidth: 160 }
        Pill { text: "−"; onPicked: root.apply([stp.key, Math.max(stp.lo, stp.value - stp.step)]) }
        Rectangle {
            Layout.fillWidth: true; implicitHeight: 4; radius: 2; color: root.c("line", "#2a2620")
            Rectangle { width: parent.width * (stp.value - stp.lo) / (stp.hi - stp.lo); height: parent.height; radius: 2; color: root.c("fg", "#a89f8c") }
        }
        Pill { text: "+"; onPicked: root.apply([stp.key, Math.min(stp.hi, stp.value + stp.step)]) }
        Text { text: stp.value + "px"; color: root.c("fg", "#a89f8c"); font { family: root.mono; pixelSize: 11 } Layout.preferredWidth: 44; horizontalAlignment: Text.AlignRight }
    }
    component Toggle: RowLayout {
        id: tg
        property string label
        property string key
        property bool value
        Layout.fillWidth: true
        Text { text: tg.label; color: root.c("fg", "#a89f8c"); font { family: root.mono; pixelSize: 11; letterSpacing: 1 } }
        Item { Layout.fillWidth: true }
        Pill { text: tg.value ? "ON" : "OFF"; on: tg.value; implicitWidth: 60; onPicked: root.apply([tg.key, tg.value ? "off" : "on"]) }
    }

    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        color: "#8c000000"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        WlrLayershell.namespace: "ashfall-panel"

        MouseArea { anchors.fill: parent; onClicked: Qt.quit() }
        Item {
            anchors.fill: parent; focus: true
            Keys.onPressed: (event) => {
                if (event.key === Qt.Key_Escape || event.key === Qt.Key_Q) Qt.quit()
                const n = parseInt(event.text)   // 1-6 picks a theme
                if (n >= 1 && root.st.themes && n <= root.st.themes.length) root.apply(["theme", root.st.themes[n - 1].id])
            }
        }

        Rectangle {
            anchors.centerIn: parent
            width: 760; height: body.implicitHeight + 48
            radius: 14; color: root.c("bg", "#0c0b09"); border.width: 1; border.color: root.c("dim", "#6e6657")
            MouseArea { anchors.fill: parent }

            ColumnLayout {
                id: body
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                spacing: 16
                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "ASHFALL HUB"; color: root.c("hi", "#c2b8a3"); font { family: root.mono; pixelSize: 14; bold: true; letterSpacing: 4 } }
                    Item { Layout.fillWidth: true }
                    Text { text: setter.running ? "applying…" : "SUPER + ALT + S"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; letterSpacing: 2 } }
                }
                Box {
                    Label { text: "THEME  ·  keys 1–6" }
                    Flow {
                        Layout.fillWidth: true; spacing: 8
                        Repeater {
                            model: root.st.themes || []
                            Pill { required property var modelData; required property int index
                                   text: (index + 1) + "  " + modelData.name; on: root.st.theme === modelData.id
                                   onPicked: root.apply(["theme", modelData.id]) }
                        }
                    }
                }
                Box {
                    Label { text: "WINDOWS" }
                    RowLayout {
                        spacing: 8
                        Repeater {
                            model: [["outline", "OUTLINE"], ["bunker", "BUNKER"], ["plate", "HEAVY PLATE"], ["monolith", "MONOLITH"]]
                            Pill { required property var modelData; text: modelData[1]; on: root.cfg.style === modelData[0]
                                   onPicked: root.apply(["style", modelData[0]]) }
                        }
                    }
                    Stepper { label: "GAPS"; key: "gaps"; value: root.cfg.gaps || 0; lo: 0; hi: 32; step: 2 }
                    Stepper { label: "CORNER RADIUS"; key: "radius"; value: root.cfg.radius || 0; lo: 0; hi: 16; step: 1 }
                }
                Box {
                    Label { text: "TERMINAL" }
                    RowLayout {
                        Layout.fillWidth: true; spacing: 8
                        Text { text: "OPACITY"; color: root.c("fg", "#a89f8c"); font { family: root.mono; pixelSize: 11; letterSpacing: 1 } Layout.preferredWidth: 160 }
                        Repeater {
                            model: [0.7, 0.8, 0.9, 1.0]
                            Pill { required property var modelData
                                   text: modelData === 1.0 ? "SOLID" : Math.round(modelData * 100) + "%"
                                   on: Math.abs((root.cfg.opacity || 1) - modelData) < 0.05
                                   onPicked: root.apply(["opacity", String(modelData)]) }
                        }
                    }
                    Toggle { label: "FROSTED BLUR BEHIND TERMINAL"; key: "blur"; value: !!root.cfg.blur }
                }
                Box {
                    Label { text: "PERFORMANCE & EXTRAS" }
                    Toggle { label: "LOW POWER MODE  (no animations, shadows, fading)"; key: "lowpower"; value: !!root.cfg.lowpower }
                    Toggle { label: "ANIMATIONS"; key: "animations"; value: root.cfg.animations !== false }
                    Toggle { label: "ASH-CHAN MASCOT"; key: "mascot"; value: root.cfg.mascot !== false }
                }
                Text { Layout.alignment: Qt.AlignHCenter; text: "changes apply instantly · Esc closes · wallpapers: Super+Alt+W"
                       color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10 } }
            }
        }
    }
}
