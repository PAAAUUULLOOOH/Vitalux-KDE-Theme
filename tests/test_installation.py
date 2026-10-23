#!/usr/bin/env python3
"""Exercise real file writes/restoration under isolated test directories."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[1] / "package/tools/manage.py"
spec = importlib.util.spec_from_file_location("liquid_glass_manage", MODULE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="liquid-glass test ")
        self.root = Path(self.temp.name)
        home = self.root / "user"
        home.mkdir()
        self.ctx = m.Context(home, home / "data", home / "config", home / "state", (self.root / "system-share",))
        self.j = m.Journal(self.ctx)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_per_key_restore_preserves_unrelated_and_later_changes(self):
        p = self.put(self.ctx.config / "kdeglobals", "# original\n[General]\nColorScheme=Before\nFont=keep\n[Icons]\nTheme=old\n")
        self.j.set(p, "[General]", "ColorScheme", "LiquidGlass")
        self.j.set(p, "[Icons]", "Theme", "LiquidGlass")
        m.ini_set(p, "[Icons]", "Theme", "ManuallyChanged")
        m.ini_set(p, "[General]", "NewUnrelated", "keep-too")
        kept = self.j.restore()
        self.assertEqual(m.ini_get(p, "[General]", "ColorScheme"), "Before")
        self.assertEqual(m.ini_get(p, "[General]", "Font"), "keep")
        self.assertEqual(m.ini_get(p, "[General]", "NewUnrelated"), "keep-too")
        self.assertEqual(m.ini_get(p, "[Icons]", "Theme"), "ManuallyChanged")
        self.assertEqual(len(kept), 1)

    def test_multiple_ini_groups_root_and_duplicate_keys(self):
        p = self.put(self.ctx.config / "sample", "[A]\nother=x\n[A][Nested]\nkey=one\nkey=two\n[Z]\nlast=y\n")
        m.ini_set(p, "[A][Nested]", "key", "new")
        m.ini_set(p, "", "root", "value")
        self.assertEqual(m.ini_get(p, "[A][Nested]", "key"), "new")
        self.assertEqual(m.ini_get(p, "", "root"), "value")
        self.assertEqual(p.read_text().count("key="), 1)
        self.assertEqual(m.ini_get(p, "[Z]", "last"), "y")

    def test_reinstall_keeps_initial_backup_and_file_permissions(self):
        p = self.put(self.ctx.data / "icons/LiquidGlass/index.theme", "original")
        p.chmod(0o640)
        self.j.put(p, b"first")
        self.j = m.Journal(self.ctx)
        self.j.put(p, b"second")
        self.j.restore()
        self.assertEqual(p.read_text(), "original")
        self.assertEqual(p.stat().st_mode & 0o777, 0o640)

    def test_fresh_install_after_uninstall_takes_a_new_baseline(self):
        p = self.put(self.ctx.data / "icons/LiquidGlass/index.theme", "baseline one")
        self.j.put(p, b"theme one")
        self.j.restore()
        self.j.path.unlink()
        p.write_text("baseline two")
        other = m.Journal(self.ctx)
        other.put(p, b"theme two")
        other.restore()
        self.assertEqual(p.read_text(), "baseline two")

    def test_unedited_browser_file_is_restored_byte_for_byte(self):
        p = self.put(self.ctx.home / "profile/user.js", '// my prefs without final newline')
        before = p.read_bytes()
        self.j.block(p, 'user_pref("test", true);')
        self.j.restore()
        self.assertEqual(p.read_bytes(), before)

    def test_plasma_script_quotes_paths_and_does_not_replace_placeholder_like_data(self):
        snapshot = {"launchers": [{"container": 1, "id": 2, "icon": "__LG_IMAGE__-IMAGE-RESTORE"}], "desktops": []}
        image = 'file:///a path/"wallpaper".jpg'
        with patch.object(m, "plasma_script") as call:
            m.change_desktop(snapshot, image)
        script = call.call_args[0][0]
        self.assertIn(json.dumps(snapshot), script)
        self.assertIn(json.dumps(image), script)

    def test_created_payload_removed_but_edited_payload_preserved(self):
        a = self.ctx.data / "theme/owned.svg"
        b = self.ctx.data / "theme/edited.svg"
        self.j.put(a, b"owned")
        self.j.put(b, b"owned")
        b.write_text("user edit")
        self.j.restore()
        self.assertFalse(a.exists())
        self.assertEqual(b.read_text(), "user edit")

    def test_foreign_paths_and_symlinks_rejected(self):
        external = self.root / "not-user/data"
        external.parent.mkdir()
        external.write_text("private")
        symlink = self.ctx.home / "linked"
        symlink.symlink_to(external)
        for p in (external, symlink):
            with self.assertRaises(RuntimeError):
                self.j.put(p, b"changed")
        self.assertEqual(external.read_text(), "private")

    def test_browser_blocks_preserve_other_customizations_and_remove_own_block(self):
        p = self.put(self.ctx.home / "profile/chrome/userChrome.css", "/* my own CSS */\n")
        self.j.block(p, "#nav-bar { color: black; }")
        self.j.block(p, "#nav-bar { color: blue; }")
        self.assertEqual(p.read_text().count(m.BEGIN), 1)
        p.write_text(p.read_text() + "/* later CSS */\n")
        self.j.restore()
        self.assertNotIn(m.BEGIN, p.read_text())
        self.assertIn("my own CSS", p.read_text())
        self.assertIn("later CSS", p.read_text())

    def test_firefox_profile_detection_native_flatpak_external_profile_excluded(self):
        for prefix in (".mozilla/firefox", ".var/app/org.mozilla.firefox/.mozilla/firefox"):
            root = self.ctx.home / prefix
            (root / "abc.default").mkdir(parents=True)
            self.put(root / "profiles.ini", "[Profile0]\nPath=abc.default\nIsRelative=1\n[Profile1]\nPath=/outside/profile\nIsRelative=0\n")
        self.assertEqual(len(list(m.firefox_profiles(self.ctx))), 2)

    def test_icon_preserves_original_mark_and_resolves_local_references(self):
        p = self.put(self.ctx.home / "native.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="lg-plate"><stop stop-color="#73ba25"/></linearGradient></defs><path id="mark" d="M0 0h32v32H0Z" fill="url(#lg-plate)"/></svg>')
        data = m.glass_icon(p)
        r = ET.fromstring(data)
        ids = [x.get("id") for x in r.iter() if x.get("id")]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(b"#73ba25", data)
        self.assertIn(b"url(#app-lg-plate)", data)
        self.assertIn("app-mark", ids)
        self.assertEqual(sum(e.tag == f"{{{m.SVG_NS}}}svg" for e in r.iter()), 1,
                         "QtSvg must receive a flattened icon, without nested SVG viewports")

    def test_icon_active_content_and_external_image_are_not_embedded(self):
        for content in ('<script>bad()</script>', '<image href="file:///private.png"/>'):
            p = self.put(self.ctx.home / "unsafe.svg", '<svg xmlns="http://www.w3.org/2000/svg">' + content + '</svg>')
            with self.assertRaises(ValueError):
                m.glass_icon(p)

    def test_real_desktop_icon_integration_does_not_change_exec(self):
        self.put(self.ctx.system_data[0] / "icons/hicolor/scalable/apps/firefox.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="15" fill="#ff7500"/></svg>')
        self.put(self.ctx.system_data[0] / "applications/firefox.desktop", "[Desktop Entry]\nName=Firefox\nIcon=firefox\nExec=firefox --private-window %u\nType=Application\n")
        m.generate_icons(self.ctx, self.j)
        self.assertTrue((self.ctx.data / "icons/LiquidGlass/scalable/apps/firefox.svg").is_file())
        self.assertFalse((self.ctx.data / "applications/firefox.desktop").exists())
        self.assertIn("--private-window", (self.ctx.system_data[0] / "applications/firefox.desktop").read_text())

    def test_no_profiles_or_app_data_deleted_by_full_round_trip(self):
        original = self.put(self.ctx.config / "kdeglobals", "[General]\nColorScheme=Before\nFont=NeverChange\n")
        private = self.put(self.ctx.home / ".mozilla/firefox/default/places.sqlite", "untouched browser data")
        root = private.parent.parent
        self.put(root / "profiles.ini", "[Profile0]\nPath=default\nIsRelative=1\n")
        with patch.object(m, "refresh_desktop"), patch.object(m, "has_kvantum", return_value=False), patch.object(m, "aurorae_plugin", return_value=None), patch.object(m.shutil, "which", return_value=None):
            m.install(self.ctx)
            m.install(self.ctx)
            self.assertEqual(m.ini_get(original, "[General]", "ColorScheme"), "LiquidGlass")
            m.uninstall(self.ctx)
        self.assertEqual(m.ini_get(original, "[General]", "ColorScheme"), "Before")
        self.assertEqual(m.ini_get(original, "[General]", "Font"), "NeverChange")
        self.assertEqual(private.read_text(), "untouched browser data")
        self.assertFalse((private.parent / "user.js").exists())
        self.assertFalse((private.parent / "chrome/userChrome.css").exists())
        self.assertFalse((self.ctx.data / "plasma/desktoptheme/liquid-glass/metadata.json").exists())

    def test_install_only_leaves_settings_and_profiles_untouched(self):
        p = self.put(self.ctx.config / "kdeglobals", "[General]\nColorScheme=Before\n")
        before = p.read_bytes()
        with patch.object(m, "refresh_desktop"), patch.object(m.shutil, "which", return_value=None):
            m.install(self.ctx, only=True)
        self.assertEqual(p.read_bytes(), before)
        self.assertFalse(m.Journal(self.ctx).doc["keys"])

    def test_install_only_does_not_override_absolute_desktop_icons(self):
        icon = self.put(self.ctx.home / "private-app.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="15" fill="red"/></svg>')
        self.put(self.ctx.system_data[0] / "applications/example.desktop", f"[Desktop Entry]\nName=Example\nIcon={icon}\nExec=example %u\n")
        m.generate_icons(self.ctx, self.j, overrides=False)
        self.assertFalse((self.ctx.data / "applications/example.desktop").exists())
        self.assertTrue((self.ctx.data / "icons/LiquidGlass/scalable/apps/liquidglass-example.svg").exists())


if __name__ == "__main__":
    unittest.main()
