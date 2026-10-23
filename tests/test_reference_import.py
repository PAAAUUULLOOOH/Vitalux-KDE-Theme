"""Import the chosen original design without executing arbitrary app code."""
import importlib.util
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    'vitalux_reference_import',
    Path(__file__).resolve().parents[1] / 'tools/import_vitalux_design.py',
)
importer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(importer)


class ReferenceImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.source = Path(self.temporary.name)
        (self.source / 'vitalux').mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, name, content):
        (self.source / 'vitalux' / name).write_text(content)

    def test_liquid_silver_values_come_from_the_source_not_a_new_palette(self):
        self.write('premium.py', "raise RuntimeError('do not execute the app')\nCOLLECTIONS['liquid_silver'] = dict(bg='#080b10', accent='#b9ccdc', title='Liquid Silver')\n")
        result = importer.extract_palette(self.source, 'liquid_silver')
        self.assertEqual(result, {'bg': '#080b10', 'accent': '#b9ccdc', 'title': 'Liquid Silver'})

    def test_base_glass_remains_a_separate_original_design(self):
        self.write('theme.py', "_THEMES = {'glass': {'bg': '#090f1b', 'card': '#18283c'}, 'light': {'bg': '#ffffff'}}\n")
        result = importer.extract_palette(self.source, 'glass')
        self.assertEqual(result['bg'], '#090f1b')
        self.assertEqual(result['card'], '#18283c')
        self.assertNotIn('accent', result)

    def test_dynamic_palette_expressions_are_rejected(self):
        self.write('premium.py', "COLLECTIONS['liquid_silver'] = calculate_palette()\n")
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            importer.extract_palette(self.source, 'liquid_silver')

    def test_missing_design_does_not_invent_a_fallback(self):
        self.write('premium.py', 'COLLECTIONS = {}\n')
        with self.assertRaisesRegex(ValueError, 'not found'):
            importer.extract_palette(self.source, 'liquid_silver')


if __name__ == '__main__':
    unittest.main()
