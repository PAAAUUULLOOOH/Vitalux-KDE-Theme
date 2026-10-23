import QtQuick
import QtQuick.Controls.Basic
TextField {
 id: field
 implicitHeight: 46
 leftPadding: 14; rightPadding: 14; topPadding: 10; bottomPadding: 10
 color: "#1d283b"; placeholderTextColor: "#6a7f9a"; selectionColor: "#007aff"; selectedTextColor: "white"
 font.pixelSize: 15
 background: Rectangle {
  radius: 13; color: "#ecffffff"
  border.width: field.activeFocus ? 2 : 1
  border.color: field.activeFocus ? "#007aff" : "#a8bfdce8"
  Behavior on border.color { ColorAnimation { duration: 160 } }
 }
}
