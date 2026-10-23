"""Application templates; every visual color comes from the Vitalux reference."""

FIREFOX = r'''
/* Vitalux Liquid Silver browser chrome. Security indicators remain visible. */
:root {
 color-scheme: dark !important;
 --lg-ink: {{text}}; --lg-line: {{border}};
 --toolbar-bgcolor: {{sidebar}} !important; --toolbar-color: {{text}} !important;
 --lwt-accent-color: {{bg}} !important; --lwt-text-color: {{text}} !important;
 --lwt-toolbarbutton-icon-fill: {{muted}} !important;
 --toolbarbutton-border-radius: 12px !important; --tab-border-radius: 12px !important;
 --tab-selected-bgcolor: {{card}} !important; --tab-selected-textcolor: {{text}} !important;
 --urlbarView-highlight-background: {{accent}} !important; --urlbarView-highlight-color: {{bg}} !important;
 --arrowpanel-background: {{card}} !important; --arrowpanel-color: {{text}} !important;
 --arrowpanel-border-color: {{border}} !important; --panel-background: {{card}} !important;
 --panel-color: {{text}} !important; --autocomplete-popup-background: {{card}} !important;
 --autocomplete-popup-color: {{text}} !important; --autocomplete-popup-highlight-background: {{accent}} !important;
 --autocomplete-popup-highlight-color: {{bg}} !important;
}
#navigator-toolbox {
 background: linear-gradient(145deg,{{card}},{{bg}}) !important; color: {{text}} !important;
 border-bottom: 1px solid {{border}} !important; box-shadow: inset 0 1px rgba({{secondary_rgb}},.16) !important;
}
#TabsToolbar, #nav-bar, #PersonalToolbar { background: transparent !important; color: {{text}} !important; }
#nav-bar { padding-block: 5px !important; box-shadow: none !important; }
.tab-background { border: 1px solid transparent !important; transition: background-color 160ms ease, border-color 160ms ease !important; }
.tab-background[selected] { background: linear-gradient(145deg,{{track}},{{sidebar}}) !important; border-color: {{border}} !important; box-shadow: inset 0 1px rgba({{secondary_rgb}},.22) !important; }
.tabbrowser-tab:hover > .tab-stack > .tab-background:not([selected]) { background: {{card}} !important; }
.tab-label, #urlbar-input, #searchbar { color: {{text}} !important; }
#urlbar-background, #searchbar {
 background: {{sidebar}} !important; border: 1px solid {{border}} !important; border-radius: 12px !important;
 box-shadow: inset 0 1px rgba({{secondary_rgb}},.10) !important;
}
#urlbar[focused] > #urlbar-background { border-color: {{accent}} !important; box-shadow: 0 0 0 2px rgba({{accent_rgb}},.14) !important; }
.urlbarView { background: {{card}} !important; color: {{text}} !important; }
.urlbarView-row-inner { border-radius: 12px !important; }
menupopup, panel { --panel-background: {{card}}; --panel-color: {{text}}; }
@media (prefers-reduced-motion: reduce) { .tab-background { transition: none !important; } }
'''

DISCORD = r'''
/**
 * @name Vitalux Liquid Silver
 * @author PAAAUUULLOOOH
 * @version {{version}}
 * @description Original Vitalux Liquid Silver palette, activated through Vencord.
 */
:root, .theme-light, .theme-dark {
 color-scheme: dark;
 --background-primary: {{bg}}; --background-secondary: {{sidebar}}; --background-secondary-alt: {{card}};
 --background-tertiary: {{bg}}; --background-floating: {{card}};
 --background-base-lowest: {{bg}}; --background-base-lower: {{sidebar}}; --background-base-low: {{card}};
 --background-surface-high: {{card}}; --background-surface-higher: {{track}};
 --background-mod-subtle: rgba({{accent_rgb}},.06); --background-modifier-hover: rgba({{accent_rgb}},.08);
 --background-modifier-selected: rgba({{accent_rgb}},.14);
 --text-normal: {{text}}; --text-primary: {{text}}; --text-muted: {{muted}}; --text-secondary: {{muted}};
 --header-primary: {{text}}; --header-secondary: {{muted}}; --channels-default: {{muted}};
 --interactive-normal: {{muted}}; --interactive-hover: {{text}}; --interactive-active: {{accent}};
 --brand-500: {{accent}}; --brand-experiment: {{accent}}; --brand-560: {{secondary}};
 --brand-experiment-500: {{accent}}; --brand-experiment-560: {{secondary}};
 --white: {{text}}; --button-filled-brand-text: {{bg}};
 --button-filled-brand-background: {{accent}}; --button-filled-brand-background-hover: {{secondary}};
 --channeltextarea-background: {{card}}; --input-background: {{sidebar}};
 --scrollbar-auto-thumb: {{border}}; --scrollbar-auto-track: transparent;
}
[class*="sidebar_"] { background: {{sidebar}}; border-right: 1px solid {{grid}}; }
[class*="chatContent_"] { background: linear-gradient(145deg,{{card}},{{bg}}); }
[class*="channelTextArea_"] { background: {{card}}; border: 1px solid {{border}}; border-radius: 21px; box-shadow: inset 0 1px rgba({{secondary_rgb}},.16); }
[class*="button_"][class*="colorBrand_"] { background: linear-gradient(145deg,{{secondary}},{{accent}}); color: {{bg}}; }
[class*="button_"][class*="colorBrand_"] [class*="contents_"] { color: {{bg}}; }
[role="dialog"], [role="menu"] { background: {{card}}; color: {{text}}; border: 1px solid {{border}}; border-radius: 21px; box-shadow: inset 0 1px rgba({{secondary_rgb}},.16), 0 12px 40px rgba(0,0,0,.3); }
'''

STEAM = r'''
/* Vitalux Liquid Silver — Millennium. Local UI styles, no remote imports. */
:root {
 color-scheme: dark; --lg-bg: {{bg}}; --lg-view: {{sidebar}}; --lg-text: {{text}};
 --lg-muted: {{muted}}; --lg-accent: {{accent}}; --lg-line: {{border}};
 --gpSystemLightestGrey: {{text}}; --gpSystemLighterGrey: {{secondary}};
 --gpSystemLightGrey: {{muted}}; --gpSystemGrey: {{border}};
 --gpSystemDarkGrey: {{track}}; --gpSystemDarkerGrey: {{sidebar}}; --gpSystemDarkestGrey: {{bg}};
 --gpStoreLightestGrey: {{text}};
}
[class*="steamdesktop_DesktopUI"], [class*="libraryhome_Container"], [class*="library_AppDetails"],
[class*="library_Container"], [class*="library_MainPanel"], .DialogContent, .DialogBody {
 background: linear-gradient(145deg,{{card}},{{bg}}) !important; color: {{text}} !important;
}
[class*="gamelistbar_Container"], [class*="gamelist_Container"], [class*="friendslist_FriendsList"], [class*="chatwindow_ChatWindow"] {
 background: {{sidebar}} !important; color: {{text}} !important; border-color: {{grid}} !important;
}
[class*="libraryhome_LibraryHome"], [class*="libraryhome_UpdatesContainer"], [class*="appdetails_Header"], [class*="library_MainPanel"] { background-color: {{bg}} !important; }
[class*="gamelistentry_Container"] { color: {{muted}} !important; border-radius: 12px; }
[class*="gamelistentry_Container"]:hover { background: {{card}} !important; color: {{text}} !important; }
[class*="gamelistentry_Selected"] { background: {{track}} !important; color: {{text}} !important; box-shadow: inset 2px 0 {{accent}}; }
[class*="libraryhome_CollectionName"], [class*="libraryhome_ShelfName"], [class*="appdetailssection_SectionHeader"], .DialogHeader, .DialogLabel { color: {{text}} !important; }
[class*="libraryhome_Shelf"], [class*="appdetailssection_Container"] { border-radius: 21px; }
.DialogButton, button.DialogButton {
 background: linear-gradient(145deg,{{track}},{{sidebar}}) !important; color: {{text}} !important;
 border: 1px solid {{border}} !important; border-radius: 12px !important;
 box-shadow: inset 0 1px rgba({{secondary_rgb}},.16); transition: border-color 160ms ease, box-shadow 160ms ease;
}
.DialogButton:hover { border-color: {{accent}} !important; }
.DialogButton.Primary, .DialogButton.Primary:hover { background: linear-gradient(145deg,{{secondary}},{{accent}}) !important; color: {{bg}} !important; }
.DialogInput, .DialogTextInputBase, input.DialogInput { background: {{sidebar}} !important; color: {{text}} !important; border: 1px solid {{border}} !important; border-radius: 12px !important; }
.DialogInput:focus { border-color: {{accent}} !important; }
[class*="appportrait_LibraryItemBox"], [class*="libraryassetimage_Container"] { border-radius: 12px; overflow: hidden; }
[class*="steamdesktop_TopBar"], [class*="steamdesktop_BottomBar"] { background: {{sidebar}} !important; color: {{text}} !important; border-color: {{grid}} !important; }
[class*="steamdesktop_TopBar"] [class*="MenuButton"], [class*="steamdesktop_BottomBar"] [class*="Status"] { color: {{text}} !important; }
@media(prefers-reduced-motion:reduce) { .DialogButton { transition: none !important; } }
'''

TEAMSPEAK = r'''
/* Vitalux Liquid Silver for TeamSpeak 3. */
QWidget { color: {{text}}; selection-background-color: {{accent}}; selection-color: {{bg}}; }
QMainWindow, QDialog { background: {{bg}}; }
QTreeView, QListView, QTextEdit, QPlainTextEdit, QTableView {
 background: {{sidebar}}; alternate-background-color: {{card}}; border: 1px solid {{border}};
 border-radius: 12px; padding: 5px;
}
QTreeView::item, QListView::item { min-height: 24px; padding: 2px 5px; border-radius: 8px; }
QTreeView::item:hover, QListView::item:hover { background: {{track}}; }
QTreeView::item:selected, QListView::item:selected { background: {{accent}}; color: {{bg}}; }
QPushButton, QToolButton, QComboBox {
 background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {{track}},stop:1 {{sidebar}});
 border: 1px solid {{border}}; border-radius: 12px; padding: 6px 12px;
}
QPushButton:hover, QToolButton:hover, QComboBox:hover { border-color: {{accent}}; }
QPushButton:pressed, QToolButton:pressed { background: {{track}}; }
QPushButton:default { border-color: {{accent}}; }
QWidget:disabled { color: {{muted}}; }
QLineEdit, QSpinBox, QDoubleSpinBox { background: {{sidebar}}; color: {{text}}; border: 1px solid {{border}}; border-radius: 12px; padding: 5px; }
QLineEdit:focus, QSpinBox:focus { border-color: {{accent}}; }
QMenu, QMenuBar { background: {{card}}; color: {{text}}; border: 1px solid {{border}}; }
QMenu::item { padding: 6px 22px; margin: 2px 5px; border-radius: 8px; }
QMenu::item:selected { background: {{accent}}; color: {{bg}}; }
QTabWidget::pane, QGroupBox { border: 1px solid {{border}}; border-radius: 21px; background: {{card}}; }
QTabBar::tab { background: {{sidebar}}; border: 1px solid {{grid}}; border-radius: 12px; padding: 6px 12px; margin: 3px; }
QTabBar::tab:selected { background: {{track}}; color: {{text}}; }
QGroupBox { margin-top: 12px; padding: 8px; }
QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle { background: {{border}}; border-radius: 4px; min-height: 24px; min-width: 24px; }
QScrollBar::handle:hover { background: {{accent}}; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QProgressBar { border: 1px solid {{grid}}; background: {{track}}; border-radius: 5px; text-align: center; }
QProgressBar::chunk { background: {{accent}}; border-radius: 4px; }
'''
