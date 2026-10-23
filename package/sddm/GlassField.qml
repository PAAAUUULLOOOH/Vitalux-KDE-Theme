import QtQuick
import QtQuick.Controls.Basic
TextField {
 id: field
 implicitHeight: 46
 leftPadding: 14; rightPadding: 14; topPadding: 10; bottomPadding: 10
 color: "#edf2f7"; placeholderTextColor: "#afbdc9"; selectionColor: "#b9ccdc"; selectedTextColor: "#080b10"
 font.pixelSize: 15
 background: Rectangle {
  radius: 12; color: "#0d1219"
  border.width: field.activeFocus ? 2 : 1
  border.color: field.activeFocus ? "#b9ccdc" : "#a073889c"
  Behavior on border.color { ColorAnimation { duration: 160 } }
 }
}
