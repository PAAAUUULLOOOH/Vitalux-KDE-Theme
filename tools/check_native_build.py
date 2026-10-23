#!/usr/bin/env python3
"""Compile every bundled native engine on openSUSE without applying a theme."""
from pathlib import Path
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'package/tools'))
import full_install as installer
import manage
import root_helper


def main():
    if os.geteuid() != 0 or not Path('/usr/bin/zypper').exists():
        raise RuntimeError('Run inside the disposable openSUSE CI container as root.')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    manage.verify_package()
    with tempfile.TemporaryDirectory(prefix='vitalux-native-') as temporary:
        directory = Path(temporary)
        context = manage.Context(directory, directory / 'data', directory / 'config', directory / 'state', ())
        stage = directory / 'stage'
        stage.mkdir()
        version = installer.build_native(context, stage, all_components=True)
        files = [path for path in stage.rglob('*') if path.is_file() or path.is_symlink()]
        for path in files:
            destination = Path('/') / path.relative_to(stage)
            if path.is_symlink() or not root_helper.permitted(destination):
                raise RuntimeError('Unexpected native install target: ' + str(destination))
        for name in ('libglass.so', 'libkwin_glass_config.so', 'libkvantum.so', 'org.kde.kwin.aurorae.v2.so', 'Kvantum.colors'):
            if not any(path.name == name for path in files):
                raise RuntimeError('Missing compiled component: ' + name)
        manage.verify_package()
        print('All bundled native components compiled and staged for KWin ' + version + '.', flush=True)
        print('Source package unchanged; all destinations passed the system allowlist.', flush=True)


if __name__ == '__main__':
    main()
