"""Verify actual Vitalux source values and safe upgrades of the former theme."""
import configparser
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'package'
sys.path.insert(0, str(PACKAGE / 'tools'))
import manage as m

spec = importlib.util.spec_from_file_location('design_reference_importer', ROOT / 'tools/import_vitalux_design.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class DesignFidelityTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((PACKAGE / 'design/vitalux.json').read_text())
        self.colors = self.document['colors']

    def test_every_palette_value_matches_the_pinned_original_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / 'vitalux').mkdir()
            (source / 'vitalux/premium.py').write_bytes((PACKAGE / 'reference/vitalux/premium.py').read_bytes())
            original = importer.extract_palette(source, 'liquid_silver')
        # JSON lists and Python tuples encode the same original series colors.
        self.assertEqual(self.colors, json.loads(json.dumps(original)))
        self.assertEqual(self.document['source']['skin'], 'liquid_silver')
        self.assertEqual(self.colors['bg'], '#080b10')
        self.assertEqual(self.colors['accent'], '#b9ccdc')

    def test_the_reference_source_files_have_not_been_rewritten(self):
        for name, expected in self.document['source']['files'].items():
            path = PACKAGE / 'reference/vitalux' / Path(name).name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, name)

    def test_plasma_palette_and_kde_palette_are_identical_and_dark(self):
        desktop = PACKAGE / 'payload/plasma/desktoptheme/liquid-glass/colors'
        palette = PACKAGE / 'payload/color-schemes/LiquidGlass.colors'
        self.assertEqual(desktop.read_bytes(), palette.read_bytes())
        config = configparser.ConfigParser()
        config.read(palette)
        expected = ','.join(str(int(self.colors['bg'][i:i + 2], 16)) for i in (1, 3, 5))
        self.assertEqual(config['Colors:Window']['BackgroundNormal'], expected)
        self.assertEqual(config['Colors:Window']['ForegroundNormal'], '237,242,247')

    def test_all_six_application_styles_use_the_original_silver_and_ink(self):
        paths = ('gtk/gtk-3.0/gtk.css', 'gtk/gtk-4.0/gtk.css',
                 'integrations/firefox/userChrome.css', 'integrations/discord/LiquidGlass.theme.css',
                 'integrations/steam/LiquidGlass/liquid-glass.css', 'integrations/teamspeak3/LiquidGlass.qss')
        for name in paths:
            content = (PACKAGE / name).read_text()
            for value in (self.colors['bg'], self.colors['text'], self.colors['accent']):
                self.assertIn(value, content, name)
            self.assertNotIn('#007aff', content.lower(), name)
            self.assertNotIn('{{', content, name)

    def test_silver_controls_keep_dark_legible_text(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(PACKAGE / 'kvantum/KvLiquidGlass/KvLiquidGlass.kvconfig')
        foreground = config['GeneralColors']['progress.indicator.text.color']
        self.assertEqual(foreground, self.colors['bg'])
        self.assertEqual(config['PanelButtonCommand']['text.toggle.color'], self.colors['bg'])
        def luminance(hex_color):
            channels = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
            return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
        contrast = (luminance(self.colors['accent']) + .05) / (luminance(foreground) + .05)
        self.assertGreater(contrast, 4.5)

    def test_upgrade_from_light_palette_keeps_the_original_uninstall_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            ctx = m.Context(home, home / 'data', home / 'config', home / 'state/liquid-glass-kde', ())
            globals_file = ctx.config / 'kdeglobals'
            globals_file.parent.mkdir(parents=True)
            globals_file.write_text('[General]\nAccentColor=73,186,37\nColorScheme=Before\n')
            journal = m.Journal(ctx)
            journal.set(globals_file, '[General]', 'AccentColor', '0,122,255')
            journal.set(globals_file, '[General]', 'ColorScheme', 'LiquidGlass')
            journal.doc['version'] = '1.0.0'
            journal.save()
            current = m.Journal(ctx)
            with patch.object(m, 'has_kvantum', return_value=True), patch.object(m, 'aurorae_plugin', return_value=None):
                m.apply_settings(ctx, current)
            self.assertEqual(m.ini_get(globals_file, '[General]', 'AccentColor'), '185,204,220')
            self.assertEqual(m.ini_get(ctx.config / 'gtk-3.0/settings.ini', '[Settings]', 'gtk-application-prefer-dark-theme'), 'true')
            current.restore()
            self.assertEqual(m.ini_get(globals_file, '[General]', 'AccentColor'), '73,186,37')
            self.assertEqual(m.ini_get(globals_file, '[General]', 'ColorScheme'), 'Before')


if __name__ == '__main__':
    unittest.main()
