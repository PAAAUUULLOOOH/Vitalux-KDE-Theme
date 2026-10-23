#!/usr/bin/env python3
"""Copy compiled theme components with a separate reversible system journal."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import manage as base


ALLOWED = (
 r"/usr/lib(?:64)?/qt6/plugins/org.kde.kdecoration3/org.kde.kwin.aurorae.v2\.so",
 r"/usr/lib(?:64)?/(?:qt6/plugins/)?(?:kwin/effects/(?:plugins/(?:lib)?glass|configs/(?:lib)?kwin_glass_config)|styles/libkvantum)\.so",
 r"/usr/lib(?:64)?/qt6/plugins/(?:kwin/effects/(?:plugins/(?:lib)?glass|configs/(?:lib)?kwin_glass_config)|styles/libkvantum)\.so",
 r"/usr/share/locale/[^/]+/LC_MESSAGES/kwin_effects_glass\.mo",
 r"/usr/share/color-schemes/Kvantum\.colors",
 r"/usr/share/sddm/themes/liquid-glass/[^\x00]*",
 r"/usr/share/icons/LiquidGlass-Cursors/[^\x00]*",
 r"/usr/lib/millennium/[^\x00]*",
 r"/usr/bin/millennium",
 r"/usr/share/(?:applications|icons|metainfo|millennium|doc)/[^\x00]*millennium[^\x00]*",
 r"/etc/sddm(?:\.conf|\.conf\.d/zz-liquid-glass\.conf)",
)


def permitted(path):
    value=str(path)
    return any(re.fullmatch(pattern,value) for pattern in ALLOWED) and '..' not in path.parts


class SystemJournal(base.Journal):
    def check(self,path):
        if not permitted(path) or path.is_symlink() or not permitted(path.resolve()):
            raise RuntimeError(f"Nicht erlaubtes Systemziel: {path}")


def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['install','uninstall','remove-vencord-grant'])
    p.add_argument('--stage',type=Path)
    p.add_argument('--sddm',action='store_true')
    p.add_argument('--grant')
    p.add_argument('--was-absent',action='store_true')
    args=p.parse_args()
    if os.geteuid()!=0:p.error('Dieser Helfer benötigt sudo.')
    # sudo may inherit a user's restrictive umask. Installed theme/plugin
    # directories must remain readable by SDDM and ordinary desktop users.
    os.umask(0o022)
    state=Path('/var/lib/liquid-glass-kde')
    state.mkdir(parents=True,mode=0o700,exist_ok=True)
    state.chmod(0o700)
    ctx=base.Context(Path('/root'),Path('/usr/share'),Path('/etc'),state,())
    with base.install_lock(ctx):
        if args.action=='remove-vencord-grant':
            if not args.grant or not re.fullmatch(r'/[^;\n]+/Vencord/dist(?::r[ow])?',args.grant):
                raise RuntimeError('Nur die konkrete Vencord-Dist-Freigabe darf zurückgenommen werden.')
            from app_themes import remove_permission_entry
            remove_permission_entry(Path('/var/lib/flatpak/overrides/com.discordapp.Discord'),args.grant,args.was_absent)
            return 0
        j=SystemJournal(ctx)
        if args.action=='uninstall':
            if not j.path.exists():return 0
            kept=j.restore()
            base.atomic_write(state/'last-uninstall.json',j.path.read_bytes(),0o600)
            j.path.unlink()
            for name in kept:print('Nachträgliche Systemänderung beibehalten:',name)
            return 0
        if not args.stage or not args.stage.is_dir():p.error('Staging-Ordner fehlt.')
        stage=args.stage.resolve()
        candidates=[f for f in stage.rglob('*') if f.is_file() or f.is_symlink()]
        # Validate the entire install plan before touching any destination.
        for f in candidates:
            target=Path('/')/f.relative_to(stage)
            if f.is_symlink() or not f.resolve().is_relative_to(stage) or not permitted(target):
                raise RuntimeError(f'Unerwarteter Bestandteil im Build: {f.relative_to(stage)}')
            j.check(target)
        for f in candidates:
            j.put(Path('/')/f.relative_to(stage),f.read_bytes(),f.stat().st_mode&0o777)
        if args.sddm:
            existing=Path('/etc/sddm.conf')
            config=existing if existing.exists() else Path('/etc/sddm.conf.d/zz-liquid-glass.conf')
            j.set(config,'[Theme]','Current','liquid-glass')
            j.set(config,'[Theme]','CursorTheme','LiquidGlass-Cursors')
            j.set(config,'[Theme]','CursorSize','32')
        print('Systemkomponenten installiert; vorhandene Dateien und Einstellungen sind gesichert.')
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,RuntimeError) as e:
        print(str(e),file=sys.stderr);sys.exit(1)
