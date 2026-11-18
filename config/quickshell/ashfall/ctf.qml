// ASHFALL — CTF panel. Super+A opens it; one plain key does each action; Esc closes.
// Runs only while open (launched by ashfall-panel), so it costs nothing when closed.
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root
    property var st: ({})
    property var pal: st.palette || ({})
    property var ch: st.challenge || ({})
    property var vpn: st.vpn || ({})
    function c(k, d) { return pal[k] !== undefined ? pal[k] : d }
    function alpha(hex, aa) { return "#" + aa + hex.slice(1) }   // "#rrggbb" -> "#aarrggbb"
    readonly property string mono: "JetBrainsMono Nerd Font"

    Process {
        running: true
        command: ["ashfall-state"]
        stdout: StdioCollector { onStreamFinished: { try { root.st = JSON.parse(text) } catch (e) {} } }
    }

    function act(cmd) {
        Quickshell.execDetached(["sh", "-c", cmd])
        Qt.quit()
    }

    readonly property var actions: [
        { k: "N", label: "NEW",       cmd: "ctf-new" },
        { k: "F", label: "FLAG",      cmd: "flag-grab" },
        { k: "R", label: "REVSHELL",  cmd: "kitty --class ashfall-scratch --hold -e revsh" },
        { k: "O", label: "NOTES",     cmd: "ctf-notes" },
        { k: "T", label: "TERMINAL",  cmd: "kitty -d \"$HOME/ctf/current\"" },
        { k: "C", label: "COPY IP",   cmd: "ctf-ip" },
        { k: "V", label: "VPN ON/OFF",cmd: "ctf-vpn" },
        { k: "L", label: "LISTEN",    cmd: "kitty -e rlwrap nc -lvnp 4444" }
    ]

    PanelWindow {
        id: win
        anchors { top: true; bottom: true; left: true; right: true }
        color: "#8c000000"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        WlrLayershell.namespace: "ashfall-panel"

        MouseArea { anchors.fill: parent; onClicked: Qt.quit() }

        Item {
            anchors.fill: parent
            focus: true
            Keys.onPressed: (event) => {
                if (event.key === Qt.Key_Escape || event.key === Qt.Key_Q) { Qt.quit(); return }
                const t = event.text.toUpperCase()
                for (const a of root.actions) if (a.k === t) { root.act(a.cmd); return }
            }
        }

        Rectangle {
            anchors.centerIn: parent
            width: 420
            height: col.implicitHeight + 44
            radius: 14
            color: root.c("bg", "#0c0b09")
            border.width: 1
            border.color: root.c("dim", "#6e6657")
            MouseArea { anchors.fill: parent }   // clicks inside don't close

            ColumnLayout {
                id: col
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 22 }
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    Text { text: "CTF"; color: root.c("hi", "#c2b8a3"); font { family: root.mono; pixelSize: 14; bold: true; letterSpacing: 4 } }
                    Item { Layout.fillWidth: true }
                    Text { text: "SUPER + A"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; letterSpacing: 2 } }
                }

                // active challenge
                Rectangle {
                    Layout.fillWidth: true; implicitHeight: chCol.implicitHeight + 24
                    radius: 10; color: "transparent"; border.width: 1; border.color: root.c("line", "#2a2620")
                    ColumnLayout {
                        id: chCol; anchors { fill: parent; margins: 12 } spacing: 5
                        Text { text: "ACTIVE CHALLENGE"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; letterSpacing: 3 } }
                        Text { text: root.ch.name || "none — press N"; color: root.c("hi", "#c2b8a3"); font { family: root.mono; pixelSize: 15; bold: true } }
                        Text {
                            visible: !!root.ch.name
                            text: (root.ch.category || "?") + " · " + (root.ch.event || "") + " · on it for " +
                                  (root.ch.minutes >= 60 ? Math.floor(root.ch.minutes / 60) + "h " : "") + ((root.ch.minutes || 0) % 60) + "m"
                            color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 11 }
                        }
                    }
                }

                // vpn
                Rectangle {
                    Layout.fillWidth: true; implicitHeight: vCol.implicitHeight + 24
                    radius: 10; color: "transparent"; border.width: 1; border.color: root.c("line", "#2a2620")
                    ColumnLayout {
                        id: vCol; anchors { fill: parent; margins: 12 } spacing: 6
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "VPN"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; letterSpacing: 3 } }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                implicitWidth: vTag.implicitWidth + 20; implicitHeight: 24; radius: 12
                                color: root.vpn.up ? root.alpha(root.c("ok", "#5d6a48"), "4d") : "transparent"
                                border.width: 1; border.color: root.vpn.up ? root.c("c10", "#74825d") : root.c("line2", "#3a352c")
                                Text { id: vTag; anchors.centerIn: parent; text: root.vpn.up ? root.vpn.iface.toUpperCase() + " UP" : "DOWN · V"
                                       color: root.vpn.up ? root.c("c10", "#74825d") : root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; bold: true } }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: root.vpn.ip || "—"; color: root.c("hi", "#c2b8a3"); font { family: root.mono; pixelSize: 14 } }
                            Item { Layout.fillWidth: true }
                            Text { text: "C to copy"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10 } }
                        }
                        Text { visible: !!root.vpn.profile; text: "profile: " + root.vpn.profile; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10 } }
                    }
                }

                // flags
                Rectangle {
                    Layout.fillWidth: true; implicitHeight: fCol.implicitHeight + 24
                    radius: 10; color: "transparent"; border.width: 1; border.color: root.c("line", "#2a2620")
                    ColumnLayout {
                        id: fCol; anchors { fill: parent; margins: 12 } spacing: 5
                        Text { text: "FLAGS"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10; letterSpacing: 3 } }
                        Repeater {
                            model: (root.ch.flags && root.ch.flags.length) ? root.ch.flags : ["none yet — F grabs one from your clipboard"]
                            Text { required property var modelData; text: modelData; elide: Text.ElideRight; Layout.fillWidth: true
                                   color: (root.ch.flags && root.ch.flags.length) ? root.c("accent2", "#9a8348") : root.c("dim", "#6e6657")
                                   font { family: root.mono; pixelSize: 11 } }
                        }
                    }
                }

                // one-key actions
                GridLayout {
                    Layout.fillWidth: true
                    columns: 4; rowSpacing: 8; columnSpacing: 8
                    Repeater {
                        model: root.actions
                        Rectangle {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true; implicitHeight: 48; radius: 10
                            color: ma.containsMouse ? root.c("line", "#2a2620") : "transparent"
                            border.width: 1; border.color: index === 0 ? root.c("fg", "#a89f8c") : root.c("line2", "#3a352c")
                            ColumnLayout {
                                anchors.centerIn: parent; spacing: 1
                                Text { Layout.alignment: Qt.AlignHCenter; text: modelData.k; color: root.c("hi", "#c2b8a3"); font { family: root.mono; pixelSize: 14; bold: true } }
                                Text { Layout.alignment: Qt.AlignHCenter; text: modelData.label; color: root.c("fg", "#a89f8c"); font { family: root.mono; pixelSize: 8; letterSpacing: 1 } }
                            }
                            MouseArea { id: ma; anchors.fill: parent; hoverEnabled: true; onClicked: root.act(modelData.cmd) }
                        }
                    }
                }
                Text { Layout.alignment: Qt.AlignHCenter; text: "one key, no modifiers · Esc closes"; color: root.c("dim", "#6e6657"); font { family: root.mono; pixelSize: 10 } }
            }
        }
    }
}
