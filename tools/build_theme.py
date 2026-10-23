#!/usr/bin/env python3
"""Generate KDE/application styles from the pinned Vitalux design reference."""
from __future__ import annotations
import configparser
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'package'
DOCUMENT = json.loads((PACKAGE / 'design/vitalux.json').read_text())
P = DOCUMENT['colors']
CONTROLS = DOCUMENT['controls']
VERSION = DOCUMENT['version']
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')


def write(relative, text):
    path = PACKAGE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n')


def rgb(value):
    return ','.join(str(int(value[i:i + 2], 16)) for i in (1, 3, 5))


def rgba(value, alpha):
    return f'rgba({rgb(value)},{alpha})'


def expand(text):
    values = dict(P, **CONTROLS, version=VERSION)
    values.update({role + '_rgb': rgb(value) for role, value in P.items()
                   if isinstance(value, str) and re.fullmatch(r'#[\da-fA-F]{6}', value)})
    return re.sub(r'\{\{(\w+)\}\}', lambda m: str(values[m[1]]), text)


def scheme():
    lines = ['[General]', 'Name=Vitalux Liquid Silver', 'ColorScheme=LiquidGlass', 'shadeSortColumn=true', '', '[KDE]', 'contrast=4', '']
    backgrounds = {'Window': 'bg', 'View': 'sidebar', 'Button': 'card', 'Header': 'sidebar', 'Tooltip': 'card', 'Selection': 'accent', 'Complementary': 'sidebar'}
    for section, background in backgrounds.items():
        selected = section == 'Selection'
        values = {
            'BackgroundNormal': CONTROLS['active_bg'] if selected else P[background], 'BackgroundAlternate': P['track'],
            'ForegroundNormal': P['text'],
            'ForegroundInactive': P['muted'],
            'ForegroundActive': P['text'] if selected else P['accent'],
            'ForegroundLink': P['accent'], 'ForegroundVisited': P['secondary'],
            'ForegroundNegative': '#f26464', 'ForegroundNeutral': '#f5b84d', 'ForegroundPositive': '#2dd4bf',
            'DecorationFocus': P['accent'], 'DecorationHover': P['secondary'],
        }
        lines.append(f'[Colors:{section}]')
        lines += [key + '=' + rgb(value) for key, value in values.items()]
        lines.append('')
    lines += ['[Colors:Header][Inactive]', 'BackgroundNormal=' + rgb(P['sidebar']), 'ForegroundNormal=' + rgb(P['muted']), '',
              '[WM]', 'activeBackground=' + rgb(P['card']), 'activeForeground=' + rgb(P['text']),
              'inactiveBackground=' + rgb(P['bg']), 'inactiveForeground=' + rgb(P['muted'])]
    text = '\n'.join(lines)
    write('payload/color-schemes/LiquidGlass.colors', text)
    write('payload/plasma/desktoptheme/liquid-glass/colors', text)


def vectors():
    """Retain the tested KSvg/Kvantum slices and replace their material roles."""
    mapping = {}
    for role, colors in {
        'card': '#ffffff #f6f9ff #f8fbff #f3f6fb #f3f7fd #f4f8ff #f7faff',
        'bg': '#f2f5fa #e9eef9 #f0f4fa',
        'sidebar': '#e5ebf4 #ebf0f7 #e9eff8',
        'track': '#deebfc #c7ddfa #d5e6fb #c8e1ff #dceaff #eff6ff #d7eaff #caddf9 #edf2fa #e2efff #cbdef7',
        'accent': '#007aff #399aff #258dff #57a6f3',
        'secondary': '#b8ddff', 'text': '#364156',
        'border': '#b6c8df #b7cee9 #347dbd', 'muted': '#a8bad0 #8a97aa',
    }.items():
        for color in colors.split():
            mapping[color] = P[role]
    mapping['#ff6c70'] = '#f26464'
    for template in (ROOT / 'tools/templates').rglob('*.svg'):
        relative = template.relative_to(ROOT / 'tools/templates')
        text = re.sub(r'#[\da-fA-F]{6}\b', lambda m: mapping.get(m[0].lower(), m[0]), template.read_text())
        root = ET.fromstring(text)
        for gradient in root.findall(f'.//{{{SVG}}}linearGradient'):
            ident = gradient.get('id')
            if ident not in ('glass', 'rim', 'quiet', 'blue'):
                continue
            stops = DOCUMENT['material']['edge'] if ident == 'rim' else DOCUMENT['material']['wash']
            if ident == 'blue':
                stops = [[0, 'secondary', 255], [1, 'accent', 255]]
            for child in list(gradient):
                gradient.remove(child)
            for position, role, alpha in stops:
                ET.SubElement(gradient, f'{{{SVG}}}stop', {'offset': str(position), 'stop-color': P[role], 'stop-opacity': f'{alpha / 255:.6f}'})
        # 9-slice margins/masks keep their protocol colors, not screen colors.
        # Original state-specific frames remain intact; translucent large
        # surfaces now use the exact Vitalux smoke-glass wash and rim stops.
        if '/widgets/' in str(relative) and any(x in template.name for x in ('background', 'tooltip', 'dialog')):
            for element in root.iter():
                if element.get('fill') in (P['card'], P['bg'], P['sidebar']):
                    element.set('fill', 'url(#glass)')
                    element.attrib.pop('fill-opacity', None)
        if 'aurorae/' in str(relative):
            for element in root.iter():
                if element.get('fill') == P['card']:
                    element.set('fill', 'url(#glass)')
        write(relative, ET.tostring(root, encoding='unicode'))


def kvantum():
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config.read(ROOT / 'tools/templates/kvantum/KvLiquidGlass/KvLiquidGlass.kvconfig')
    general = config['%General']
    general.update(comment='Original Vitalux Liquid Silver palette and smoked glass', contrast='1.0', intensity='1.0', saturation='1.0')
    config['GeneralColors'] = {
        'window.color': P['bg'], 'base.color': P['sidebar'], 'alt.base.color': P['card'],
        'button.color': CONTROLS['button_bg'], 'light.color': P['secondary'], 'mid.light.color': P['track'],
        'dark.color': P['bg'], 'mid.color': P['border'], 'highlight.color': CONTROLS['active_bg'],
        'inactive.highlight.color': P['track'], 'text.color': P['text'], 'window.text.color': P['text'],
        'button.text.color': P['text'], 'disabled.text.color': P['muted'], 'highlight.text.color': P['text'],
        'tooltip.base.color': P['card'], 'tooltip.text.color': P['text'],
        'link.color': P['accent'], 'link.visited.color': P['secondary'],
        'progress.indicator.text.color': P['bg'], 'progress.inactive.indicator.text.color': P['bg'],
    }
    for section in config.sections():
        for key in list(config[section]):
            if key.startswith('text.') and key.endswith('.color'):
                config[section][key] = P['bg'] if key == 'text.toggle.color' else P['text']
    # A selected row is silver; the symbol/text inside it must remain dark.
    for section in ('CheckBox', 'RadioButton', 'ProgressbarContents'):
        config[section]['text.normal.color'] = P['text']
    import io
    output = io.StringIO()
    config.write(output, space_around_delimiters=False)
    write('kvantum/KvLiquidGlass/KvLiquidGlass.kvconfig', output.getvalue())


def gtk():
    # Both GTK generations use one source palette. GTK4 also exposes modern
    # libadwaita variables, used by ProtonPlus rather than a Qt-only approximation.
    named = {
        'window_bg_color': 'bg', 'window_fg_color': 'text', 'view_bg_color': 'sidebar', 'view_fg_color': 'text',
        'headerbar_bg_color': 'sidebar', 'headerbar_fg_color': 'text', 'sidebar_bg_color': 'sidebar',
        'sidebar_fg_color': 'muted', 'secondary_sidebar_bg_color': 'card', 'secondary_sidebar_fg_color': 'text',
        'card_bg_color': 'card', 'card_fg_color': 'text', 'dialog_bg_color': 'card', 'dialog_fg_color': 'text',
        'popover_bg_color': 'card', 'popover_fg_color': 'text', 'accent_bg_color': 'accent',
        'accent_fg_color': 'bg', 'accent_color': 'accent', 'theme_bg_color': 'bg', 'theme_fg_color': 'text',
        'theme_base_color': 'sidebar', 'theme_text_color': 'text', 'theme_selected_bg_color': 'accent',
        'theme_selected_fg_color': 'bg', 'insensitive_fg_color': 'muted',
    }
    definitions = '\n'.join(f'@define-color {name} {P[role]};' for name, role in named.items())
    shared = expand('''
window, dialog, .background { background-color: {{bg}}; color: {{text}}; }
headerbar, .titlebar {
 background-image: linear-gradient(140deg,{{card}},{{sidebar}}); color: {{text}};
 border-bottom: 1px solid alpha({{border}},.55); box-shadow: inset 0 1px alpha({{secondary}},.20);
}
button { border-radius: 12px; color: {{text}}; transition: background-color 160ms ease, box-shadow 160ms ease; }
button:not(.flat):not(.suggested-action):not(.destructive-action) {
 background-image: linear-gradient(alpha({{secondary}},.08),alpha({{bg}},.12));
 background-color: {{card}}; border: 1px solid alpha({{border}},.65);
 box-shadow: inset 0 1px alpha({{secondary}},.16), inset 0 -1px alpha({{bg}},.6);
}
button:hover { border-color: {{accent}}; box-shadow: inset 0 0 0 1px alpha({{accent}},.16); }
button:active, button:checked { background-color: {{track}}; }
button.suggested-action { background-image: linear-gradient({{secondary}},{{accent}}); color: {{bg}}; border-color: {{accent}}; }
entry, searchentry, spinbutton { background: {{sidebar}}; color: {{text}}; border-radius: 12px; border: 1px solid {{border}}; }
entry:focus, entry:focus-within { border-color: {{accent}}; outline-color: alpha({{accent}},.3); }
treeview, textview text, .view { background-color: {{sidebar}}; color: {{text}}; }
.navigation-sidebar, .sidebar, .sidebar-pane { background-color: {{sidebar}}; color: {{muted}}; }
.card, .boxed-list { background: {{card}}; color: {{text}}; border-radius: 21px; box-shadow: inset 0 1px alpha({{secondary}},.18); }
.boxed-list > row { color: {{text}}; }
.boxed-list > row:hover { background: alpha({{accent}},.10); }
menu, popover > contents, dialog, .dialog { background-color: {{card}}; color: {{text}}; border: 1px solid alpha({{border}},.55); border-radius: 21px; }
menuitem { border-radius: 8px; margin: 2px 5px; }
menuitem:hover, *:selected { background-color: {{accent}}; color: {{bg}}; }
scale trough, progressbar trough { background: {{track}}; border-color: {{grid}}; border-radius: 5px; }
scale highlight, progressbar progress { background: {{accent}}; border-color: {{accent}}; border-radius: 5px; }
scale slider { background-image: linear-gradient({{secondary}},{{accent}}); border-color: {{border}}; }
switch { border-radius: 12px; background: {{track}}; }
switch:checked { background: {{accent}}; }
switch slider { border-radius: 50%; background: {{text}}; }
notebook header { background: {{sidebar}}; }
notebook tab:checked { background: {{card}}; }
scrollbar slider { background-color: {{border}}; border-radius: 6px; }
scrollbar slider:hover { background-color: {{accent}}; }
tooltip { background: {{card}}; color: {{text}}; border: 1px solid {{border}}; border-radius: 12px; }
*:disabled { color: {{muted}}; opacity: .55; }
''')
    write('gtk/gtk-3.0/gtk.css', '@import url("resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained-dark.css");\n' + definitions + '\n' + shared)
    variables = ':root {\n' + '\n'.join(f' --{name.replace("_", "-")}: {P[role]};' for name, role in named.items()) + '\n color-scheme: dark;\n}\n'
    write('gtk/gtk-4.0/gtk.css', variables + definitions + '\n' + shared)


def metadata():
    for path in (PACKAGE / 'payload').rglob('metadata.json'):
        data = json.loads(path.read_text())
        if 'KPlugin' in data:
            data['KPlugin'].update(Name='Vitalux Liquid Silver', Version=VERSION,
                                  Description='Original Vitalux Liquid Silver: smoked glass, satin silver and its original atmosphere',
                                  License='LicenseRef-Vitalux')
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    path = PACKAGE / 'payload/plasma/desktoptheme/liquid-glass/plasmarc'
    text = path.read_text()
    text = re.sub(r'^contrast=.*$', 'contrast=1.0', text, flags=re.M)
    text = re.sub(r'^intensity=.*$', 'intensity=1.0', text, flags=re.M)
    text = re.sub(r'^saturation=.*$', 'saturation=1.0', text, flags=re.M)
    path.write_text(text)


def applications():
    from application_styles import FIREFOX, DISCORD, STEAM, TEAMSPEAK
    for path, text in (
        ('integrations/firefox/userChrome.css', FIREFOX),
        ('integrations/discord/LiquidGlass.theme.css', DISCORD),
        ('integrations/steam/LiquidGlass/liquid-glass.css', STEAM),
        ('integrations/teamspeak3/LiquidGlass.qss', TEAMSPEAK),
    ):
        write(path, expand(text))
    path = PACKAGE / 'integrations/steam/LiquidGlass/skin.json'
    data = json.loads(path.read_text())
    data.update(name='Vitalux Liquid Silver', version=VERSION,
                description='Original Vitalux Liquid Silver: smoked glass and satin silver.')
    path.write_text(json.dumps(data, indent=2) + '\n')
    path = PACKAGE / 'payload/aurorae/themes/liquid-glass/liquid-glassrc'
    text = path.read_text()
    text = re.sub(r'^ActiveTextColor=.*$', 'ActiveTextColor=' + rgb(P['text']), text, flags=re.M)
    text = re.sub(r'^InactiveTextColor=.*$', 'InactiveTextColor=' + rgb(P['muted']), text, flags=re.M)
    path.write_text(text)


def qml():
    mapping = {}
    for role, values in {
        'bg': '#1c61bc #1c61bc #193558',
        'card': '#f1f5fb #edf4ff #faffff #faffff',
        'sidebar': '#ffffff #ecffffff #dfeafa',
        'text': '#1d283b #203859 #ecf5ff',
        'muted': '#6a7f9a',
        'accent': '#007aff #0068e0 #0873d7 #439fff',
        'secondary': '#2795ff', 'track': '#d5e5fb',
    }.items():
        for value in values.split():
            mapping[value] = P[role]
    mapping.update({
        '#100d3059': '#12080b10', '#b3eff5ff': '#b9' + P['card'][1:],
        '#eaffffff': '#7d' + P['secondary'][1:], '#a8bfdce8': '#a0' + P['border'][1:],
        '#9fbedfe8': '#a0' + P['border'][1:], '#a8273f': '#f26464',
        '#bdeff5ff': '#b9' + P['card'][1:], '#dfffffff': '#7d' + P['secondary'][1:],
        '#3093b4dc': '#80' + P['track'][1:],
    })
    for template in (ROOT / 'tools/templates/sddm').glob('*.qml'):
        text = re.sub(r'#[\da-fA-F]{6,8}\b', lambda m: mapping.get(m[0].lower(), m[0]), template.read_text())
        text = text.replace('radius: 32', 'radius: 25').replace('radius: 13', 'radius: 12')
        text = text.replace('palette.highlightedText: "#ffffff"', f'palette.highlightedText: "{P["bg"]}"')
        text = text.replace('palette.highlightedText: "' + P['sidebar'] + '"', f'palette.highlightedText: "{P["bg"]}"')
        text = text.replace('button.highlighted ? "white"', 'button.highlighted ? "' + P['bg'] + '"')
        text = text.replace('selectedTextColor: "white"', 'selectedTextColor: "' + P['bg'] + '"')
        text = text.replace('color: "white"; font.pixelSize: 60', 'color: "' + P['text'] + '"; font.pixelSize: 60')
        if template.name == 'Main.qml':
            overlay = 'Rectangle { anchors.fill: parent; radius: 25; color: "#b9' + P['card'][1:] + '"; border.color: "#7d' + P['secondary'][1:] + '"; border.width: 1 }'
            wash = '\n'.join(f'GradientStop {{ position: {t}; color: "#{alpha:02x}{P[role][1:]}" }}' for t, role, alpha in DOCUMENT['material']['strong_wash'])
            replacement = 'Rectangle { anchors.fill: parent; radius: 25; gradient: Gradient { ' + wash + ' }\n border.color: "#7d' + P['secondary'][1:] + '"; border.width: 1 }\n'
            replacement += 'Rectangle { anchors.fill: parent; anchors.margins: 2; radius: 23; color: "transparent"; border.color: "#14ffffff"; border.width: 1 }'
            if overlay not in text:
                raise ValueError('SDDM material template changed')
            text = text.replace(overlay, replacement)
            text = text.replace('text: "openSUSE"; color: "' + P['bg'] + '"', 'text: "openSUSE"; color: "' + P['text'] + '"')
        write('sddm/' + template.name, text)
    template = ROOT / 'tools/templates/splash/Splash.qml'
    text = re.sub(r'#[\da-fA-F]{6,8}\b', lambda m: mapping.get(m[0].lower(), m[0]), template.read_text())
    text = text.replace('radius: 34', 'radius: 25').replace('text: "openSUSE"; color: "' + P['bg'] + '"', 'text: "openSUSE"; color: "' + P['text'] + '"')
    write('payload/plasma/look-and-feel/io.github.PAAAUUULLOOOH.LiquidGlass/contents/splash/Splash.qml', text)


def other_metadata():
    for relative in ('sddm/metadata.desktop', 'payload/aurorae/themes/liquid-glass/metadata.desktop'):
        path = PACKAGE / relative
        text = path.read_text()
        text = re.sub(r'^Name=.*$', 'Name=Vitalux Liquid Silver', text, flags=re.M)
        text = re.sub(r'^(Version|X-KDE-PluginInfo-Version)=.*$', lambda m: m[1] + '=' + VERSION, text, flags=re.M)
        text = text.replace('License=MIT', 'License=LicenseRef-Vitalux')
        text = text.replace('Clear glass for openSUSE Tumbleweed', 'Original Vitalux Liquid Silver for openSUSE Tumbleweed')
        path.write_text(text)
    for relative in ('payload/icons/LiquidGlass/index.theme', 'payload/icons/LiquidGlass-Cursors/index.theme'):
        path = PACKAGE / relative
        text = path.read_text().replace('Name=Liquid Glass\n', 'Name=Vitalux Liquid Silver\n')
        text = text.replace('Inherits=breeze,hicolor', 'Inherits=breeze-dark,breeze,hicolor')
        path.write_text(text)


def main():
    scheme()
    vectors()
    kvantum()
    gtk()
    metadata()
    applications()
    qml()
    other_metadata()
    print('Generated desktop materials from', DOCUMENT['source']['display_name'], DOCUMENT['source']['commit'])


if __name__ == '__main__':
    main()
