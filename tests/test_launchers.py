"""Exercise graphical entry points and shell logging without modifying a desktop."""
import configparser
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="KDE theme O'Connor ü ")
        self.directory = Path(self.temporary.name)
        self.package = self.directory / 'Extracted theme'
        self.package.mkdir()
        self.bin = self.directory / 'bin'
        self.bin.mkdir()
        self.env = os.environ.copy()
        for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'VITALUX_THEME_TERMINAL'):
            self.env.pop(key, None)
        self.env.update(XDG_STATE_HOME=str(self.directory / 'state'),
                        PATH=str(self.bin) + os.pathsep + self.env['PATH'],
                        VITALUX_TEST_ARGS=str(self.directory / 'args.json'))

    def tearDown(self):
        self.temporary.cleanup()

    def executable(self, path, content):
        path.write_text(content)
        path.chmod(0o755)

    def test_desktop_entry_starts_the_adjacent_script_for_paths_and_file_urls(self):
        for action, entry in (('install', 'Theme installieren.desktop'), ('uninstall', 'Theme deinstallieren.desktop')):
            for folder in (ROOT, ROOT / 'package'):
                config = configparser.ConfigParser(interpolation=None)
                config.read(folder / entry)
                section = config['Desktop Entry']
                self.assertEqual(section['Terminal'], 'true')
                source = self.package / entry
                shutil.copyfile(folder / entry, source)
                self.executable(self.package / (action + '.sh'),
                                '#!/bin/bash\nprintf "%s\\n" "$@" > "$VITALUX_TEST_ARGS"\n')
                for location in (str(source), source.as_uri()):
                    command = [location if word == '%k' else word for word in shlex.split(section['Exec'])]
                    subprocess.run(command, env=self.env, check=True, capture_output=True, timeout=10)
                    self.assertEqual(Path(self.env['VITALUX_TEST_ARGS']).read_text(), '--desktop\n')

    def test_shell_starter_opens_konsole_and_preserves_arguments(self):
        shutil.copyfile(ROOT / 'package/run-installer.sh', self.package / 'run-installer.sh')
        self.executable(self.bin / 'konsole', '#!' + sys.executable + '\nimport json,os,sys\n'
                        "open(os.environ['VITALUX_TEST_ARGS'],'w').write(json.dumps([sys.argv[1:],os.environ['VITALUX_THEME_TERMINAL']]))\n")
        self.env['DISPLAY'] = ':test'
        result = subprocess.run(['bash', str(self.package / 'run-installer.sh'), 'install', '--no-firefox'],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        args, marker = json.loads(Path(self.env['VITALUX_TEST_ARGS']).read_text())
        self.assertEqual(args, ['--separate', '--hold', '-e', 'bash', str(self.package / 'run-installer.sh'), 'install', '--no-firefox'])
        self.assertEqual(marker, '1')

    def test_terminal_output_is_logged_and_failure_status_survives_tee(self):
        shutil.copyfile(ROOT / 'package/run-installer.sh', self.package / 'run-installer.sh')
        self.executable(self.bin / 'python3', '#!/bin/bash\nprintf "actual build error\\n" >&2\nexit 23\n')
        result = subprocess.run(['bash', str(self.package / 'run-installer.sh'), 'install', '--yes'],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        log = self.directory / 'state/liquid-glass-kde/install.log'
        self.assertIn('actual build error', result.stdout)
        self.assertIn('actual build error', log.read_text())
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)

    def test_uninstaller_has_a_separate_log_and_no_recursive_terminal_launch(self):
        shutil.copyfile(ROOT / 'package/run-installer.sh', self.package / 'run-installer.sh')
        self.executable(self.bin / 'python3', '#!/bin/bash\nprintf "%s\\n" "$@"\n')
        self.env.update(DISPLAY=':test', VITALUX_THEME_TERMINAL='1')
        result = subprocess.run(['bash', str(self.package / 'run-installer.sh'), 'uninstall'],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = self.directory / 'state/liquid-glass-kde/uninstall.log'
        self.assertIn('full_install.py\nuninstall', log.read_text())
        self.assertFalse((log.parent / 'install.log').exists())


if __name__ == '__main__':
    unittest.main()
