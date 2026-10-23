"""Install app-facing themes and preserve unrelated app preferences."""
from pathlib import Path
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import manage as b


def steam_roots(ctx):
    paths=(ctx.home/'.steam/steam',ctx.data/'Steam',ctx.home/'.local/share/Steam',ctx.home/'.var/app/com.valvesoftware.Steam/.local/share/Steam')
    seen=set()
    for p in paths:
        if p.is_dir() and p.resolve() not in seen:
            seen.add(p.resolve())
            yield p.resolve()


def steam_is_flatpak(root):
    return 'com.valvesoftware.Steam' in root.parts


def vencord_roots(ctx):
    roots=[ctx.config/'Vencord',ctx.config/'Vesktop']
    flat=ctx.home/'.var/app/com.discordapp.Discord/config/Vencord'
    if flat.parent.exists():roots.append(flat)
    return roots


def loader_plan(ctx):
    entries=list(b.desktop_entries(ctx))
    discord=any('discord' in (name+' '+ident).lower() for _,ident,name,_ in entries)
    vc=discord_is_patched(ctx)
    roots=list(steam_roots(ctx))
    missing_steam=[p for p in roots if not (p/'ubuntu12_64/libmillennium_hhx64.so').is_file()]
    return {'discord_installed':discord,'vencord_needed':discord and not vc,'steam_roots':[str(p) for p in roots],'millennium_needed':[str(p) for p in missing_steam]}


def discord_resources(ctx):
    roots=[Path('/usr/share/discord'),Path('/usr/lib64/discord'),Path('/opt/discord'),ctx.data/'discord']
    for export in (ctx.home/'.local/share/flatpak/app',Path('/var/lib/flatpak/app')):
        base=export/'com.discordapp.Discord/current/active/files'
        roots.extend((base/'discord',base/'extra/discord',base/'lib/discord'))
    for root in roots:
        archive=root/'resources/app.asar'
        if archive.exists():yield archive


def discord_is_patched(ctx):
    for archive in discord_resources(ctx):
        try:
            with archive.open('rb') as f:data=f.read(65536)
            if b'Vencord' in data and b'patcher' in data:return True
        except OSError:pass
    return False


def discord_permission_snapshot(ctx):
    result=[]
    for scope,path in [('user',ctx.data/'flatpak/overrides/com.discordapp.Discord'),('system',Path('/var/lib/flatpak/overrides/com.discordapp.Discord'))]:
        value=b.ini_get(path,'[Context]','filesystems') if path.exists() else None
        result.append({'scope':scope,'path':str(path),'existed':path.exists(),'entries':[x for x in (value or '').split(';') if x]})
    return result


def new_discord_permissions(before,after):
    result=[]
    for old,new in zip(before,after):
        for value in new['entries']:
            if value not in old['entries'] and value.split(':',1)[0].endswith('/Vencord/dist'):
                result.append({'scope':new['scope'],'path':new['path'],'grant':value,'existed':old['existed']})
    return result


def remove_permission_entry(path,grant,was_absent):
    if not path.exists():return
    value=b.ini_get(path,'[Context]','filesystems') or ''
    items=[x for x in value.split(';') if x]
    if grant not in items:return
    items=[x for x in items if x!=grant]
    b.ini_set(path,'[Context]','filesystems',';'.join(items)+';' if items else None)
    if was_absent and not any('=' in line and not line.lstrip().startswith(('#',';')) for line in path.read_text().splitlines()):path.unlink()


def snapshot_loader_files(folder):
    result={}
    if folder.exists():
        for path in folder.rglob('*'):
            if path.is_symlink():raise RuntimeError('Symlink im App-Loader-Ordner wird nicht verändert: '+str(path))
            if path.is_file():result[str(path)]={'data':path.read_bytes(),'mode':path.stat().st_mode&0o777}
    return result


def adopt_loader_files(journal,folder,before):
    # The upstream installer performs these writes. Add their real footprint to
    # our journal afterwards, retaining the true pre-install baseline.
    for path in folder.rglob('*') if folder.exists() else []:
        if not path.is_file() or path.is_symlink():continue
        journal.check(path)
        ident=str(path);content=path.read_bytes()
        if ident in journal.doc['files']:
            journal.doc['files'][ident]['installed']=hashlib.sha256(content).hexdigest()
            continue
        old=before.get(ident)
        if old and old['data']==content:continue
        backup=None
        if old:
            backup=journal.doc['generation']+'/'+hashlib.sha256(ident.encode()).hexdigest()
            b.atomic_write(journal.ctx.state/'backups'/backup,old['data'],0o600)
        journal.doc['files'][ident]={'backup':backup,'mode':old['mode'] if old else path.stat().st_mode&0o777,'installed':hashlib.sha256(content).hexdigest()}
    journal.save()


def install(ctx,journal,firefox=True):
    b.integrate_apps(ctx,journal,firefox)
    # GTK4's user stylesheet has the required precedence for libadwaita apps,
    # including ProtonPlus. No global sandbox permission is needed.
    gtk4=(b.PACKAGE/'gtk/gtk-4.0/gtk.css').read_text()
    journal.block(ctx.config/'gtk-4.0/gtk.css',gtk4)
    for app in ('com.vysp3r.ProtonPlus','org.gnome.Calculator','org.gnome.TextEditor','org.gnome.Nautilus'):
        config=ctx.home/'.var/app'/app/'config'
        if config.exists():journal.block(config/'gtk-4.0/gtk.css',gtk4)
    discord_css=(b.PACKAGE/'integrations/discord/LiquidGlass.theme.css').read_text()
    for root in vencord_roots(ctx):
        if root.exists() or root.name=='Vencord' and root.parent==ctx.config:
            journal.block(root/'settings/quickCss.css',discord_css)
            journal.json_set(root/'settings/settings.json',('useQuickCss',),True)
            journal.json_set(root/'settings/settings.json',('enabledThemes',),[])
            journal.json_set(root/'settings/settings.json',('themeLinks',),[])
    steam_css=(b.PACKAGE/'integrations/steam/LiquidGlass/liquid-glass.css').read_bytes()
    skin=(b.PACKAGE/'integrations/steam/LiquidGlass/skin.json').read_bytes()
    for root in steam_roots(ctx):
        journal.put(root/'millennium/themes/LiquidGlass/skin.json',skin)
        journal.put(root/'millennium/themes/LiquidGlass/liquid-glass.css',steam_css)
        config=ctx.config/'millennium/config.json'
        if steam_is_flatpak(root):
            config=ctx.home/'.var/app/com.valvesoftware.Steam/config/millennium/config.json'
        journal.json_set(config,('themes','activeTheme'),'LiquidGlass')
        journal.json_set(config,('themes','allowedStyles'),True)
        journal.json_set(config,('general','injectCSS'),True)
        old=config.parent/'themes.json'
        if old.exists():journal.json_set(old,('active',),'LiquidGlass')
    # Qt's standard -stylesheet argument applies the TS3 stylesheet at launch
    # without editing its live SQLite settings database.
    stylesheet=ctx.data/'liquid-glass/apps/TeamSpeak3.qss'
    journal.put(stylesheet,(b.PACKAGE/'integrations/teamspeak3/LiquidGlass.qss').read_bytes())
    for path,ident,name,_ in b.desktop_entries(ctx):
        if not any(x in (name+' '+ident).lower() for x in ('teamspeak','ts3client')):continue
        existing=ctx.data/'applications'/ident
        source=existing if existing.exists() else path
        lines=source.read_text().splitlines(keepends=True)
        group='';out=[]
        for line in lines:
            if line.strip().startswith('['):group=line.strip()
            if group=='[Desktop Entry]' and line.startswith('Exec=') and ' -stylesheet ' not in line:
                value=line.split('=',1)[1].rstrip('\n')
                # Desktop Entry arguments use double-quote escaping, not shell
                # quoting. The path is a single literal argument.
                arg='"'+str(stylesheet).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')+'"'
                line='Exec='+value+' -stylesheet '+arg+'\n'
            out.append(line)
        journal.put(existing,''.join(out).encode())
    journal.doc['app_theme_version']=b.VERSION
    journal.save()


def apply_millennium_links(ctx,journal,root,runtime=Path('/usr/lib/millennium')):
    for relative,name in [('ubuntu12_32/libXtst.so.6','libmillennium_bootstrap_x86.so'),('ubuntu12_64/libXtst.so.6','libmillennium_bootstrap_hhx64.so'),('ubuntu12_64/libmillennium_hhx64.so','libmillennium_hhx64.so')]:
        journal.link(root/relative,runtime/name)


def apply_flatpak_millennium(ctx,journal,root):
    # Flatpak Steam persists ~/.local/share/Steam inside its own app data. Keep
    # all loader files there and use relative links: no host-library or home
    # directory sandbox permission is added.
    runtime=root/'liquid-glass-runtime'
    for relative,name in [('ubuntu12_32/libXtst.so.6','libmillennium_bootstrap_x86.so'),('ubuntu12_64/libXtst.so.6','libmillennium_bootstrap_hhx64.so'),('ubuntu12_64/libmillennium_hhx64.so','libmillennium_hhx64.so')]:
        journal.link(root/relative,Path('../liquid-glass-runtime')/name)
    inside=ctx.home/'.local/share/Steam/liquid-glass-runtime/libmillennium_x86.so'
    for path,ident,name,_ in b.desktop_entries(ctx):
        if ident!='com.valvesoftware.Steam.desktop':continue
        destination=ctx.data/'applications'/ident
        source=destination if destination.exists() else path
        text=source.read_text()
        env='--env=MILLENNIUM_RUNTIME_PATH="'+str(inside).replace('\\','\\\\').replace('"','\\"')+'" '
        out=[]
        for line in text.splitlines(keepends=True):
            if line.startswith('Exec=') and 'com.valvesoftware.Steam' in line and 'MILLENNIUM_RUNTIME_PATH=' not in line:
                line=line.replace('com.valvesoftware.Steam',env+'com.valvesoftware.Steam',1)
            out.append(line)
        journal.put(destination,''.join(out).encode())


def copy_brand_to_splash(ctx,journal):
    icon=ctx.data/'icons/LiquidGlass/scalable/places/liquidglass-opensuse.svg'
    if not icon.exists():
        raise RuntimeError('Das installierte openSUSE-Originalsymbol wurde nicht gefunden. Branding-Paket prüfen.')
    wallpaper=ctx.data/'wallpapers/LiquidGlass/contents/images/3840x2160.jpg'
    assets=ctx.data/f'plasma/look-and-feel/{b.GLOBAL_ID}/contents/assets'
    journal.put(assets/'opensuse.svg',icon.read_bytes())
    journal.put(assets/'wallpaper.jpg',wallpaper.read_bytes())


GLASS_SETTINGS={
 'PhysicallyBasedRefraction':'true','RefractionStrength':'5','RefractionEdgeSize':'1.4',
 'RefractionRGBFringing':'0','RimSpecular':'true','RimWidth':'12','RimSpecularScale':'2',
 'EdgeLighting':'false','BlurStrength':'4','DockBlurStrength':'2','DecorationBlurStrength':'3',
 'NoiseStrength':'0','DockNoiseStrength':'0','DecorationNoiseStrength':'0','BlurDecorations':'true',
 'BlurMenus':'true','BlurDocks':'true','DockCornerRadius':'18','MenuCornerRadius':'18',
 'Brightness':'1.0','Contrast':'1.0','Saturation':'1.0',
 'FakeBlur':'false','RoundCornersOfMaximizedWindows':'false',
}


def configure_glass(ctx,journal,version):
    settings=dict(GLASS_SETTINGS, TintColor='#12'+b.design_reference()['colors']['bg'][1:])
    for key,value in settings.items():journal.set(ctx.config/'kwinrc','[Effect-blurplus]',key,value)
    # Autostart checks the *running* KWin version before replacing native blur.
    # KWin never loads an old binary automatically after a Tumbleweed upgrade.
    journal.set(ctx.config/'kwinrc','[Plugins]','glassEnabled','false')
    journal.set(ctx.config/'kwinrc','[Plugins]','blurEnabled','true')
    runner=ctx.data/'liquid-glass/guard.py'
    journal.put(runner,(b.PACKAGE/'tools/glass_guard.py').read_bytes(),0o755)
    journal.put(ctx.state/'glass-build.json',(json.dumps({'kwin_version':version,'version':b.VERSION},indent=2)+'\n').encode(),0o600)
    escaped=str(runner).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')
    desktop=f'[Desktop Entry]\nType=Application\nName=Liquid Glass compositor\nExec=python3 "{escaped}"\nOnlyShowIn=KDE;\nX-KDE-autostart-after=panel\n'
    journal.put(ctx.config/'autostart/liquid-glass-compositor.desktop',desktop.encode())
