import QtQuick
import QtQuick.Controls.Basic
Button {
 id: button
 implicitHeight: 46; leftPadding: 18; rightPadding: 18
 contentItem: Text { text: button.text; font.pixelSize: 15; font.weight: Font.Medium; color: button.highlighted ? "#080b10" : "#edf2f7"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
 opacity: enabled ? 1 : .55
 background: Rectangle {
  radius: 12
  gradient: Gradient {
   GradientStop { position: 0; color: button.highlighted ? (button.down ? "#b9ccdc" : "#e3edf5") : (button.down ? "#2a3543" : "#151b23") }
   GradientStop { position: 1; color: button.highlighted ? "#b9ccdc" : "#0d1219" }
  }
  border.width: button.visualFocus ? 2 : 1
  border.color: button.visualFocus ? "#b9ccdc" : (button.highlighted ? "#b9ccdc" : "#a073889c")
 }
}
