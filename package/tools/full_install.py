#!/usr/bin/env python3
"""Complete openSUSE install: build matching native components and apply app themes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

import manage as b
import app_themes as apps

DEVEL = [
 'cmake-full','gcc-c++','make','gettext-tools','kf6-extra-cmake-modules','kwin6-devel','libepoxy-devel',
 'cmake(Qt6Core)','cmake(Qt6Gui)','cmake(Qt6DBus)','cmake(Qt6Widgets)',
 'cmake(Qt6OpenGL)','cmake(Qt6Network)','cmake(Qt6Xml)','cmake(Qt6Quick)','cmake(Qt6Svg)',
 'cmake(Qt6UiTools)','cmake(KF6Config)','cmake(KF6CoreAddons)','cmake(KF6GuiAddons)',
 'cmake(KF6I18n)','cmake(KF6KCMUtils)','cmake(KF6WindowSystem)','cmake(KDecoration3)',
 'cmake(KF6Svg)','cmake(KWinDBusInterface)','pkgconfig(xcb)',
]


def command(args,**kwargs):
    print('+ '+' '.join(str(x) for x in args),flush=True)
    subprocess.run([str(x) for x in args],check=True,**kwargs)


def kwin_version():
    program=shutil.which('kwin_wayland')
    if not program:raise RuntimeError('KWin Wayland wurde nicht gefunden. Ziel ist Plasma 6.8.0 / Wayland.')
    text=b.run([program,'--version'])
    match=re.search(r'\b(6\.8\.\d+(?:[\w.+~-]*)?)\b',text)
    if not match:raise RuntimeError('Dieses Paket ist für KWin 6.8.x ausgelegt. Gefunden: '+text)
    return match[1]


def require_opensuse():
    text=Path('/etc/os-release').read_text()
    if not re.search(r'^ID=["\']?opensuse-tumbleweed',text,re.M):
        raise RuntimeError('Die vollständige Installation ist für openSUSE Tumbleweed ausgelegt.')
    if platform.machine()!='x86_64':raise RuntimeError('Die Steam-/Discord-Loader werden hier für x86_64 mitgeliefert.')
    if os.environ.get('XDG_SESSION_TYPE')=='x11':
        raise RuntimeError('Der native KWin-6.8-Glaseffekt benötigt die Plasma-Wayland-Sitzung. Bitte dort anmelden.')
    kwin_version()


def fetch(ctx,name):
    spec=json.loads((b.PACKAGE/'external-manifest.json').read_text())[name]
    dest=ctx.state/'downloads'/spec['filename'];dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists() or b.digest(dest)!=spec['sha256']:
        temporary=dest.with_name(dest.name+'.part')
        try:
            with urllib.request.urlopen(spec['url'],timeout=45) as response,temporary.open('wb') as out:
                size=0
                while chunk:=response.read(1024*1024):
                    size+=len(chunk)
                    if size>100*1024*1024:raise RuntimeError('Unerwartet großer Download: '+name)
                    out.write(chunk)
            if b.digest(temporary)!=spec['sha256']:raise RuntimeError('Prüfsumme des offiziellen Downloads stimmt nicht: '+name)
            os.replace(temporary,dest)
        finally:temporary.unlink(missing_ok=True)
    return dest


def extract_runtime(archive,stage):
    """Only expected regular Millennium runtime files; never tar.extractall."""
    with tarfile.open(archive,'r:gz') as tar:
        members=tar.getmembers()
        total=0
        for member in members:
            if member.isdir():continue
            relative=PurePosixPath(member.name)
            parts=tuple(x for x in relative.parts if x!='.')
            if not member.isfile() or parts[:3]!=('usr','lib','millennium') or len(parts)!=4 or relative.is_absolute() or '..' in parts:
                raise RuntimeError('Unerwartete Datei im Millennium-Archiv: '+member.name)
            total+=member.size
            if member.size>50*1024*1024 or total>100*1024*1024:raise RuntimeError('Millennium-Archiv ist unerwartet groß.')
        for member in members:
            if member.isdir():continue
            dest=stage/Path(*PurePosixPath(member.name).parts)
            source=tar.extractfile(member)
            b.atomic_write(dest,source.read(),member.mode&0o755)


def build_native(ctx,stage):
    print('\n[1/5] Passende Build-Abhängigkeiten aus deinen eingerichteten openSUSE-Repositories installieren.',flush=True)
    dependencies=list(DEVEL)
    if not b.dbus_program():dependencies.append('/usr/lib64/qt6/bin/qdbus')
    command(['sudo','zypper','--non-interactive','install','--no-recommends',*dependencies])
    version=kwin_version() # package installation may update the installed KWin
    sources=['kwin-effects-glass']
    if not b.has_kvantum():sources.append('Kvantum')
    if not b.aurorae_plugin():sources.append('aurorae-v2')
    for name in sources:
        print('Native Komponente bauen: '+name,flush=True)
        source=b.PACKAGE/'vendor'/name
        build=ctx.state/'build'/name
        build.mkdir(parents=True,exist_ok=True)
        command(['cmake','--fresh','-S',source,'-B',build,'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_INSTALL_PREFIX=/usr','-DGLASS_WAYLAND=ON','-DGLASS_X11=OFF'])
        command(['cmake','--build',build,'--parallel',str(min(4,os.cpu_count() or 2))])
        env=os.environ.copy();env['DESTDIR']=str(stage)
        command(['cmake','--install',build],env=env)
    if not any(stage.rglob('libglass.so')) and not any(stage.rglob('glass.so')):raise RuntimeError('Der KWin-Glaseffekt wurde nicht erzeugt. Installation wird nicht als vollständig markiert.')
    return version


def sddm_stage(ctx,stage):
    if not shutil.which('sddm') and not Path('/usr/share/sddm').exists():return False
    dest=stage/'usr/share/sddm/themes/liquid-glass'
    shutil.copytree(b.PACKAGE/'sddm',dest,dirs_exist_ok=True)
    assets=dest/'assets';assets.mkdir(exist_ok=True)
    shutil.copytree(b.PACKAGE/'payload/icons/LiquidGlass-Cursors',stage/'usr/share/icons/LiquidGlass-Cursors',dirs_exist_ok=True)
    icon=ctx.data/'icons/LiquidGlass/scalable/places/liquidglass-opensuse.svg'
    if not icon.exists():raise RuntimeError('Das Original-openSUSE-Logo fehlt; SDDM wird nicht mit einem Ersatzlogo eingerichtet.')
    shutil.copy2(icon,assets/'opensuse.svg')
    shutil.copy2(b.PACKAGE/'payload/wallpapers/LiquidGlass/contents/images/3840x2160.jpg',assets/'wallpaper.jpg')
    # SDDM runs as its own unprivileged user. Sources extracted from a private
    # ZIP directory must become readable theme assets in /usr/share.
    for path in dest.rglob('*'):
        if path.is_file():path.chmod(0o644)
    for path in (stage/'usr/share/icons/LiquidGlass-Cursors').rglob('*'):
        if path.is_file():path.chmod(0o644)
    return True


def install_loaders(ctx,journal,plan,stage):
    if plan['millennium_needed']:
        archive=fetch(ctx,'millennium')
        native=[p for p in plan['millennium_needed'] if not apps.steam_is_flatpak(Path(p))]
        if native:extract_runtime(archive,stage)
        flat=[Path(p) for p in plan['millennium_needed'] if apps.steam_is_flatpak(Path(p))]
        if flat:
            unpacked=ctx.state/'flatpak-runtime-stage'
            if unpacked.exists():shutil.rmtree(unpacked)
            extract_runtime(archive,unpacked)
            for root in flat:
                runtime=root/'liquid-glass-runtime'
                for source in (unpacked/'usr/lib/millennium').iterdir():
                    journal.put(runtime/source.name,source.read_bytes(),source.stat().st_mode&0o777)
        journal.doc['millennium_added']=True
        journal.save()
    if plan['vencord_needed']:
        installer=fetch(ctx,'vencord');installer.chmod(0o755)
        journal.doc['vencord_added']=True
        journal.save()
        # Use the upstream patcher so its own backup/unpatch logic remains intact.
        # It detects native and Flatpak Discord locations; no token/account access.
        before=apps.discord_permission_snapshot(ctx)
        files_before=apps.snapshot_loader_files(ctx.config/'Vencord/dist')
        environment=os.environ.copy();environment['VENCORD_USER_DATA_DIR']=str(ctx.config/'Vencord')
        try:
            result=subprocess.run([str(installer),'--install','--branch','stable'],text=True,capture_output=True,env=environment)
            if result.returncode:
                error=result.stdout+'\n'+result.stderr
                if re.search(r'permission|access denied|operation not permitted',error,re.I):
                    command(['sudo','env','VENCORD_USER_DATA_DIR='+str(ctx.config/'Vencord'),installer,'--install','--branch','stable'])
                    journal.doc['vencord_used_sudo']=True
                else:raise RuntimeError('Der offizielle Vencord-Installer ist fehlgeschlagen:\n'+error[-3000:])
        finally:
            apps.adopt_loader_files(journal,ctx.config/'Vencord/dist',files_before)
            permissions=apps.new_discord_permissions(before,apps.discord_permission_snapshot(ctx))
            journal.doc.setdefault('vencord_permissions',[]).extend(p for p in permissions if p not in journal.doc.get('vencord_permissions',[]))
            journal.save()
        if not apps.discord_is_patched(ctx):
            raise RuntimeError('Discords Theme-Loader konnte nach der Installation nicht im Client bestätigt werden. Die Installation wird nicht als vollständig markiert.')
        journal.save()


def preflight_apps(ctx,yes):
    plan=apps.loader_plan(ctx)
    if plan['vencord_needed'] or plan['millennium_needed']:
        print('\nFür die vollständigen App-Oberflächen werden zusätzlich eingerichtet:')
        if plan['vencord_needed']:print('  Discord: Vencord (offizieller Installer, mit eigener Rücknahme).')
        if plan['millennium_needed']:print('  Steam: Millennium 3.6.2, Original-Client wird durch dessen Theme-Loader ergänzt.')
        print('Beide Apps müssen währenddessen geschlossen sein. Downloads werden per SHA-256 geprüft.')
        if not yes:
            if not sys.stdin.isatty():raise RuntimeError('Für die zusätzlichen App-Loader ist eine Bestätigung im Terminal nötig; alternativ explizit --yes verwenden.')
            if input('Diese App-Erweiterungen einrichten? [j/N] ').strip().lower() not in ('j','ja','y','yes'):
                raise RuntimeError('Keine Änderungen vorgenommen. Vollständige App-Anpassung benötigt die angezeigten Theme-Loader.')
    return plan


def close_check(ctx,plan):
    # Read process names owned by this user only; never terminate applications.
    names=set()
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if p.stat().st_uid==os.getuid():names.add((p/'comm').read_text().strip().lower())
        except OSError:pass
    blocked=[]
    if plan['discord_installed'] and any(x.startswith('discord') for x in names):blocked.append('Discord')
    if plan['steam_roots'] and any(x in ('steam','steamwebhelper') for x in names):blocked.append('Steam')
    if blocked:raise RuntimeError('Bitte '+', '.join(blocked)+' vollständig beenden und install.sh erneut starten. Es werden keine Prozesse erzwungen beendet.')


def install(ctx,args):
    require_opensuse()
    plan=preflight_apps(ctx,args.yes)
    close_check(ctx,plan)
    stage=ctx.state/'system-stage'
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir(parents=True)
    version=build_native(ctx,stage)
    # A complete application requires the actual user's active Plasma session;
    # do not silently omit the launcher/wallpaper step from a TTY/SSH session.
    snapshot=b.desktop_snapshot()
    initial=b.Journal(ctx)
    if initial.doc['desktop'] is None:initial.doc['desktop']=snapshot;initial.save()
    print('\n[2/5] Benutzer-Theme, Original-Icons und Desktop-Komponenten installieren.',flush=True)
    b.install(ctx,only=True)
    journal=b.Journal(ctx)
    # Install-only preserves app launchers; full application can now add the
    # necessary overrides using the same original baseline journal.
    b.generate_icons(ctx,journal,overrides=True)
    apps.copy_brand_to_splash(ctx,journal)
    print('\n[3/5] App-Loader und Anmelde-Design vorbereiten.',flush=True)
    install_loaders(ctx,journal,plan,stage)
    has_sddm=sddm_stage(ctx,stage)
    journal.doc['system_components']=True;journal.save()
    command(['sudo','python3',b.PACKAGE/'tools/root_helper.py','install','--stage',stage,*(['--sddm'] if has_sddm else [])])
    if not b.has_kvantum():raise RuntimeError('Der installierte Kvantum-Qt6-Stil ist nicht auffindbar. Die Installation wird nicht als vollständig gemeldet.')
    if not b.aurorae_plugin():raise RuntimeError('Der Aurorae-Fensterrahmen-Renderer ist nicht auffindbar. Die Installation wird nicht als vollständig gemeldet.')
    defaults=(ctx.data/f'plasma/look-and-feel/{b.GLOBAL_ID}/contents/defaults')
    text=(b.PACKAGE/f'payload/plasma/look-and-feel/{b.GLOBAL_ID}/contents/defaults').read_text()
    text=text.replace('widgetStyle=Breeze','widgetStyle=kvantum').replace('library=org.kde.kwin.aurorae.v2','library='+b.aurorae_plugin())
    journal.put(defaults,text.encode())
    print('\n[4/5] Plasma, GTK3/4, Firefox, TeamSpeak, Discord und Steam anwenden.',flush=True)
    # Snapshot existing desktops before making live changes.
    b.apply_settings(ctx,journal)
    apps.install(ctx,journal,not args.no_firefox)
    for path in plan['millennium_needed']:
        root=Path(path)
        if apps.steam_is_flatpak(root):apps.apply_flatpak_millennium(ctx,journal,root)
        else:apps.apply_millennium_links(ctx,journal,root)
    apps.configure_glass(ctx,journal,version)
    journal.doc['wallpaper']=(ctx.data/'wallpapers/LiquidGlass/contents/images/3840x2160.jpg').as_uri()
    if snapshot:b.change_desktop(snapshot,journal.doc['wallpaper'])
    journal.doc['full_install_version']=b.VERSION;journal.doc['version']=b.VERSION;journal.save()
    (ctx.state/'glass.pending').unlink(missing_ok=True)
    b.refresh_desktop()
    print('\n[5/5] Vollständige Installation abgeschlossen. Einmal ab- und anmelden. Danach ist der native Glaseffekt aktiv.',flush=True)
    print('Alle ursprünglichen Benutzer- und Systemdateien sind für uninstall.sh gesichert.')


def unload_effect():
    dbus=b.dbus_program()
    if not dbus:return
    for method,effect in [('unloadEffect','glass'),('loadEffect','blur')]:
        try:b.run([dbus,'org.kde.KWin','/Effects','org.kde.kwin.Effects.'+method,effect])
        except (OSError,subprocess.SubprocessError):pass


def uninstall(ctx):
    journal=b.Journal(ctx)
    if not journal.path.exists():print('Keine Benutzerinstallation gefunden.');return
    unload_effect()
    if journal.doc.get('vencord_added'):
        installer=fetch(ctx,'vencord');installer.chmod(0o755)
        args=[installer,'--uninstall','--branch','stable']
        if apps.discord_is_patched(ctx):
            command((['sudo','env','VENCORD_USER_DATA_DIR='+str(ctx.config/'Vencord')] if journal.doc.get('vencord_used_sudo') else [])+args)
        for permission in journal.doc.get('vencord_permissions',[]):
            if permission['scope']=='user':
                apps.remove_permission_entry(Path(permission['path']),permission['grant'],not permission['existed'])
            else:
                command(['sudo','python3',b.PACKAGE/'tools/root_helper.py','remove-vencord-grant','--grant',permission['grant'],*(['--was-absent'] if not permission['existed'] else [])])
    # Preserve backups until both removals have succeeded. System components
    # can be restored even if this was a partial/failed full installation.
    if journal.doc.get('system_components'):
        command(['sudo','python3',b.PACKAGE/'tools/root_helper.py','uninstall'])
    b.uninstall(ctx)
    for name in ('glass.pending','glass-status.txt'):(ctx.state/name).unlink(missing_ok=True)
    print('Zusätzliche Distribution-Buildpakete bleiben installiert; vorhandene App-Daten bleiben erhalten.')


def main():
    p=argparse.ArgumentParser(description='Liquid Glass — vollständiges KDE-Theme für openSUSE Tumbleweed / Plasma 6.8')
    p.add_argument('action',choices=['install','uninstall','status'])
    p.add_argument('--check',action='store_true')
    p.add_argument('--yes',action='store_true',help='Die angezeigten zusätzlichen App-Loader ausdrücklich freigeben')
    p.add_argument('--no-firefox',action='store_true')
    args=p.parse_args()
    if os.geteuid()==0:p.error('Ohne sudo starten. Nur die Systemkomponenten fragen gezielt nach deinem Passwort.')
    ctx=b.Context.current()
    if args.action=='install':b.verify_package()
    if args.check or args.action=='status':
        print('Vitalux Liquid Silver '+b.VERSION+' — Plasma 6.8 / openSUSE Tumbleweed')
        target_ok=True
        try:require_opensuse();print('Zielsystem: OK')
        except RuntimeError as error:
            target_ok=False
            print('Zielsystem:',error)
        print('Kvantum Qt6:',b.has_kvantum())
        print('App-Integration:',json.dumps(apps.loader_plan(ctx),ensure_ascii=False))
        print('Glaseffekt:',(ctx.state/'glass-status.txt').read_text().strip() if (ctx.state/'glass-status.txt').exists() else 'Noch nicht gestartet')
        return 0 if target_ok or args.action=='status' else 2
    with b.install_lock(ctx):
        if args.action=='install':install(ctx,args)
        else:uninstall(ctx)
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError,EOFError) as error:
        print('\nInstallation nicht abgeschlossen: '+str(error)+'\nSicherungen bleiben erhalten. Rückgängig: bash uninstall.sh',file=sys.stderr)
        sys.exit(1)
