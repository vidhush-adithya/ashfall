// ASHFALL — wallpaper + theme picker (Super+Alt+W).
// ← → browse · Enter: wallpaper + matching theme · Shift+Enter: wallpaper only · Esc closes.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root
    property var pal: ({})
    property var walls: []
    readonly property var cur: (list.currentIndex >= 0 && list.currentIndex < walls.length) ? walls[list.currentIndex] : null
    readonly property string mono: "JetBrainsMono Nerd Font"
    function c(k, d) { return pal[k] !== undefined ? pal[k] : d }

    Process {
        running: true
        command: ["ashfall-state"]
        stdout: StdioCollector { onStreamFinished: { try { root.pal = JSON.parse(text).palette || {} } catch (e) {} } }
    }
    Process {
        running: true
        command: ["ashfall-wall", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.walls = JSON.parse(text)
                    for (let i = 0; i < root.walls.length; i++) if (root.walls[i].current) list.currentIndex = i
                } catch (e) {}
            }
        }
    }
    function choose(keepTheme) {
        const w = cur
        if (!w) return
        Quickshell.execDetached(keepTheme ? ["ashfall-wall", "set", w.path, "--keep-theme"] : ["ashfall-wall", "set", w.path])
        Qt.quit()
    }

    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        color: "#b3000000"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        WlrLayershell.namespace: "ashfall-panel"

        MouseArea { anchors.fill: parent; onClicked: Qt.quit() }

        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width
            spacing: 26

            ListView {
                id: list
                Layout.fillWidth: true
                Layout.preferredHeight: 460
                orientation: ListView.Horizontal
                model: root.walls
                spacing: 22
                focus: true
                highlightRangeMode: ListView.StrictlyEnforceRange
                preferredHighlightBegin: width / 2 - 125
                preferredHighlightEnd: width / 2 + 125
                highlightMoveDuration: 220
                keyNavigationWraps: true
                Keys.onPressed: (event) => {
                    if (event.key === Qt.Key_Escape || event.key === Qt.Key_Q) Qt.quit()
                    else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) root.choose(event.modifiers & Qt.ShiftModifier)
                    else if (event.key === Qt.Key_H) list.decrementCurrentIndex()
                    else if (event.key === Qt.Key_L) list.incrementCurrentIndex()
                }
                delegate: Item {
                    id: card
                    required property var modelData
                    required property int index
                    readonly property real off: (x - list.contentX + width / 2 - list.width / 2) / 260
                    width: 250; height: 460
                    z: 100 - Math.abs(off) * 10
                    Rectangle {
                        anchors.centerIn: parent
                        width: card.index === list.currentIndex ? 250 : 200
                        height: card.index === list.currentIndex ? 440 : 360
                        radius: 12; clip: true
                        color: root.c("panel", "#14120f")
                        border.width: 1
                        border.color: card.index === list.currentIndex ? root.c("hi", "#c2b8a3") : root.c("line", "#2a2620")
                        opacity: Math.max(0.35, 1 - Math.abs(card.off) * 0.18)
                        Behavior on width { NumberAnimation { duration: 160 } }
                        Behavior on height { NumberAnimation { duration: 160 } }
                        transform: Rotation { origin.x: 125; origin.y: 220; axis { x: 0; y: 1; z: 0 }
                                              angle: Math.max(-40, Math.min(40, -card.off * 14)) }
                        Image {
                            anchors { fill: parent; margins: 1 }
                            source: "file://" + card.modelData.thumb
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            sourceSize.width: 480       // keeps memory low
                        }
                        MouseArea { anchors.fill: parent; onClicked: { if (list.currentIndex === card.index) root.choose(false); else list.currentIndex = card.index } }
                    }
                }
            }

            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.cur ? root.cur.name.toUpperCase().replace(/-/g, " ") : "loading…"
                    color: root.c("hi", "#c2b8a3"); font { family: root.mono; pixelSize: 16; bold: true; letterSpacing: 6 }
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: (root.cur && root.cur.theme ? "theme: " + root.cur.theme + "  ·  " : "")
                          + "← → browse · Enter apply · Shift+Enter wallpaper only · Esc"
                    color: root.c("fg", "#a89f8c"); font { family: root.mono; pixelSize: 11; letterSpacing: 1 }
                }
            }
        }
    }
}
