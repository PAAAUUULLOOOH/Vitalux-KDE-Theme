#!/usr/bin/env python3
"""Load only a matching KWin effect; retain native blur after an OS update."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def run(dbus,*args):
    return subprocess.run([dbus,*args],text=True,capture_output=True,timeout=15,check=True).stdout.strip()


def main():
    home=Path.home(); state=Path(os.environ.get('XDG_STATE_HOME',str(home/'.local/state')))/'liquid-glass-kde'
    build=json.loads((state/'glass-build.json').read_text())
    dbus=next((shutil.which(x) for x in ('qdbus6','qdbus-qt6','qdbus') if shutil.which(x)),None)
    if not dbus:
        dbus=next((str(x) for x in (Path('/usr/lib64/qt6/bin/qdbus'),Path('/usr/lib/qt6/bin/qdbus')) if x.exists()),None)
    if not dbus:return 1
    info=''
    for _ in range(15):
        try:info=run(dbus,'org.kde.KWin','/KWin','org.kde.KWin.supportInformation');break
        except (subprocess.SubprocessError,OSError):time.sleep(.5)
    version=re.search(r'KWin version:\s*(\S+)',info)
    pending=state/'glass.pending'
    if not version or version[1]!=build['kwin_version'] or pending.exists():
        (state/'glass-status.txt').write_text('Native Blur active. KWin changed or previous effect startup did not finish. Run install.sh to rebuild.\n')
        try:run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.loadEffect','blur')
        except (subprocess.SubprocessError,OSError):pass
        return 0
    pending.write_text(version[1])
    try:
        result=run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.loadEffect','glass')
        loaded=run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.loadedEffects')
        if 'glass' not in loaded.splitlines():raise RuntimeError('Glass effect was not loaded')
        run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.unloadEffect','blur')
        # Keep the pending marker briefly so an early compositor crash disables
        # the custom effect at next login, instead of creating a crash loop.
        time.sleep(8)
        run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.loadedEffects')
        pending.unlink(missing_ok=True)
        (state/'glass-status.txt').write_text('Glass active for KWin '+version[1]+'\n')
    except (subprocess.SubprocessError,OSError,RuntimeError) as error:
        try:run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.unloadEffect','glass')
        except (subprocess.SubprocessError,OSError):pass
        try:run(dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.loadEffect','blur')
        except (subprocess.SubprocessError,OSError):pass
        pending.unlink(missing_ok=True)
        (state/'glass-status.txt').write_text('Native blur active: '+str(error)+'\n')
        return 1
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,subprocess.SubprocessError):raise SystemExit(1)
