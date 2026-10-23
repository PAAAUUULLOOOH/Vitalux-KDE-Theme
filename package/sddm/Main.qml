import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Effects

Pane {
 id: root
 width: 1920; height: 1080; padding: 0
 background: Rectangle { color: "#080b10" }
 palette.window: "#151b23"
 palette.windowText: "#edf2f7"
 palette.text: "#edf2f7"
 palette.base: "#0d1219"
 palette.button: "#151b23"
 palette.buttonText: "#edf2f7"
 palette.highlight: "#b9ccdc"
 palette.highlightedText: "#080b10"
 readonly property bool de: Qt.locale().name.indexOf("de") === 0
 property bool busy: false
 property string message: ""
 Image { id: wallpaper; anchors.fill: parent; source: "assets/wallpaper.jpg"; fillMode: Image.PreserveAspectCrop }
 Rectangle { anchors.fill: parent; color: "#12080b10" }
 Column {
  anchors.top: parent.top; anchors.topMargin: parent.height*.09; anchors.horizontalCenter: parent.horizontalCenter; spacing: 5
  Text { id: clock; anchors.horizontalCenter: parent.horizontalCenter; color: "#edf2f7"; font.pixelSize: 60; font.weight: Font.Light; text: Qt.formatTime(new Date(),"hh:mm") }
  Text { id: date; anchors.horizontalCenter: parent.horizontalCenter; color: "#edf2f7"; font.pixelSize: 17; text: Qt.formatDate(new Date(),Qt.DefaultLocaleLongDate) }
 }
 Timer { interval: 1000; running: true; repeat: true; onTriggered: { clock.text=Qt.formatTime(new Date(),"hh:mm"); date.text=Qt.formatDate(new Date(),Qt.DefaultLocaleLongDate); } }
 Rectangle {
  id: card
  width: Math.min(400,root.width*.88); height: form.implicitHeight+64; radius: 25
  anchors.centerIn: parent; color: "transparent"
  ShaderEffectSource { id: crop; sourceItem: wallpaper; sourceRect: Qt.rect(card.x,card.y,card.width,card.height); textureSize: Qt.size(card.width,card.height); visible: false; live: true }
  Rectangle { id: mask; anchors.fill: parent; radius: 25; color: "white"; visible: false; layer.enabled: true }
  MultiEffect { anchors.fill: parent; source: crop; blurEnabled: true; blurMax: 32; blur: .65; autoPaddingEnabled: false; maskEnabled: true; maskSource: mask }
  Rectangle { anchors.fill: parent; radius: 25; gradient: Gradient { GradientStop { position: 0; color: "#b9151b23" }
GradientStop { position: 0.45; color: "#d7080b10" }
GradientStop { position: 1; color: "#d2151b23" } }
 border.color: "#7de3edf5"; border.width: 1 }
Rectangle { anchors.fill: parent; anchors.margins: 2; radius: 23; color: "transparent"; border.color: "#14ffffff"; border.width: 1 }
  ColumnLayout {
   id: form; anchors.fill: parent; anchors.margins: 32; spacing: 14
   Image { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 82; Layout.preferredHeight: 82; source: "assets/opensuse.svg"; fillMode: Image.PreserveAspectFit }
   Label { Layout.alignment: Qt.AlignHCenter; text: "openSUSE"; color: "#edf2f7"; font.pixelSize: 26 }
   GlassField { id: username; Layout.fillWidth: true; placeholderText: de ? "Benutzername" : "Username"; text: typeof userModel !== "undefined" ? userModel.lastUser : ""; enabled: !root.busy; Accessible.name: placeholderText; onAccepted: password.forceActiveFocus() }
   GlassField { id: password; Layout.fillWidth: true; placeholderText: de ? "Passwort" : "Password"; echoMode: TextInput.Password; enabled: !root.busy; Accessible.name: placeholderText; onAccepted: login.clicked() }
   ComboBox { id: session; Layout.fillWidth: true; implicitHeight: 46; model: typeof sessionModel !== "undefined" ? sessionModel : ["Plasma (Wayland)"]; textRole: typeof sessionModel !== "undefined" ? "name" : ""; currentIndex: typeof sessionModel !== "undefined" ? sessionModel.lastIndex : 0; enabled: !root.busy; Accessible.name: de ? "Sitzung" : "Session"; background: Rectangle { radius: 12; color: "#0d1219"; border.color: "#a073889c" } }
   Label { Layout.fillWidth: true; text: root.message; visible: text.length>0; color: "#f26464"; wrapMode: Text.WordWrap; Accessible.role: Accessible.AlertMessage }
   GlassButton { id: login; Layout.fillWidth: true; text: root.busy ? (de ? "Anmelden …" : "Signing in …") : (de ? "Anmelden" : "Sign in"); enabled: !root.busy && username.text.length>0; highlighted: true
    onClicked: { if(!enabled)return; if(typeof sddm === "undefined"){root.message="Preview mode";return;} root.busy=true; root.message=""; sddm.login(username.text,password.text,session.currentIndex); }
   }
  }
 }
 Row {
  anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 35; spacing: 15
  GlassButton { text: de ? "Neustart" : "Restart"; visible: typeof sddm !== "undefined" && sddm.canReboot; onClicked: sddm.reboot() }
  GlassButton { text: de ? "Ausschalten" : "Shut down"; visible: typeof sddm !== "undefined" && sddm.canPowerOff; onClicked: sddm.powerOff() }
 }
 Connections {
  target: typeof sddm !== "undefined" ? sddm : null
  function onLoginFailed() { root.busy=false; root.message=root.de ? "Anmeldung fehlgeschlagen. Bitte erneut versuchen." : "Sign-in failed. Please try again."; password.clear(); password.forceActiveFocus(); }
  function onLoginSucceeded() { password.clear(); }
 }
 Component.onCompleted: { if(username.text.length>0)password.forceActiveFocus();else username.forceActiveFocus(); }
}
