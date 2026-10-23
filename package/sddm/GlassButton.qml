import QtQuick
import QtQuick.Controls.Basic
Button {
 id: button
 implicitHeight: 46; leftPadding: 18; rightPadding: 18
 contentItem: Text { text: button.text; font.pixelSize: 15; font.weight: Font.Medium; color: button.highlighted ? "white" : "#203859"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
 opacity: enabled ? 1 : .55
 background: Rectangle {
  radius: 13
  gradient: Gradient {
   GradientStop { position: 0; color: button.highlighted ? (button.down ? "#0873d7" : "#2795ff") : (button.down ? "#d5e5fb" : "#faffff") }
   GradientStop { position: 1; color: button.highlighted ? "#0068e0" : "#dfeafa" }
  }
  border.width: button.visualFocus ? 2 : 1
  border.color: button.visualFocus ? "#007aff" : (button.highlighted ? "#439fff" : "#9fbedfe8")
 }
}
