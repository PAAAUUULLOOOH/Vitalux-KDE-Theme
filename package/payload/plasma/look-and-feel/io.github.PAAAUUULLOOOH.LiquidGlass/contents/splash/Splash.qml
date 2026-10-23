import QtQuick
Rectangle {
 id: root
 property int stage: 0
 color: "#080b10"
 Image { anchors.fill: parent; source: "../assets/wallpaper.jpg"; fillMode: Image.PreserveAspectCrop }
 Rectangle {
  id: card; anchors.centerIn: parent; width: Math.min(380, parent.width*.8); height: 270
  radius: 25; color: "#b9151b23"; border.color: "#7de3edf5"; border.width: 1
  opacity: root.stage > 0 ? 1 : 0
  scale: root.stage > 0 ? 1 : .96
  Behavior on opacity { NumberAnimation { duration: 550; easing.type: Easing.OutCubic } }
  Behavior on scale { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }
  Image { id: brand; width: 100; height: 100; anchors.horizontalCenter: parent.horizontalCenter; y: 40; source: "../assets/opensuse.svg"; fillMode: Image.PreserveAspectFit }
  Text { anchors.top: brand.bottom; anchors.topMargin: 12; anchors.horizontalCenter: parent.horizontalCenter; text: "openSUSE"; color: "#edf2f7"; font.pixelSize: 27; font.weight: Font.Medium }
  Rectangle { x: 75; y: 220; width: parent.width-150; height: 4; radius: 2; color: "#802a3543"
   Rectangle { height: 4; width: parent.width*Math.max(.08,Math.min(1,root.stage/6)); radius: 2; color: "#b9ccdc"; Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.InOutCubic } } }
  }
 }
}
