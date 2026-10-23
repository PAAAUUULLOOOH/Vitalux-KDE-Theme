import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parents[1]/'package/tools'
sys.path.insert(0,str(TOOLS))
import manage as b
import app_themes as apps
import full_install as full
import root_helper as root
import glass_guard as guard


class FullThemeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='Liquid Glass full test ')
        self.home=Path(self.temp.name)/'user';self.home.mkdir()
        self.ctx=b.Context(self.home,self.home/'data',self.home/'config',self.home/'state/liquid-glass-kde',(self.home/'system-share',))
        self.j=b.Journal(self.ctx)

    def tearDown(self):self.temp.cleanup()

    def put(self,path,text):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);return path

    def test_json_restore_keeps_unrelated_and_subsequent_preferences(self):
        p=self.put(self.ctx.config/'millennium/config.json',json.dumps({'themes':{'activeTheme':'Before'},'plugins':{'keep':True}}))
        self.j.json_set(p,('themes','activeTheme'),'LiquidGlass')
        data=json.loads(p.read_text());data['plugins']['new']=42;p.write_text(json.dumps(data))
        self.j.restore();data=json.loads(p.read_text())
        self.assertEqual(data['themes']['activeTheme'],'Before')
        self.assertEqual(data['plugins'],{'keep':True,'new':42})

    def test_json_manual_change_is_not_overwritten(self):
        p=self.ctx.config/'settings.json';self.j.json_set(p,('useQuickCss',),True)
        p.write_text('{"useQuickCss": false, "keep": 5}')
        self.j.restore();self.assertEqual(json.loads(p.read_text()),{'useQuickCss':False,'keep':5})

    def test_links_restore_both_original_files_and_original_symlinks(self):
        folder=self.home/'Steam/ubuntu12_64';folder.mkdir(parents=True)
        a=self.put(folder/'libXtst.so.6','original binary')
        c=folder/'other';c.symlink_to('../original.so')
        self.j.link(a,'/usr/lib/millennium/libmillennium_bootstrap_hhx64.so')
        self.j.link(c,'/usr/lib/millennium/libmillennium_hhx64.so')
        self.j.restore()
        self.assertEqual(a.read_text(),'original binary')
        self.assertTrue(c.is_symlink());self.assertEqual(str(c.readlink()),'../original.so')

    def test_upstream_loader_files_restore_original_content_and_remove_new_files(self):
        folder=self.ctx.config/'Vencord/dist'
        old=self.put(folder/'patcher.js','old inactive loader')
        before=apps.snapshot_loader_files(folder)
        old.write_text('updated loader');new=self.put(folder/'new.js','new loader file')
        apps.adopt_loader_files(self.j,folder,before)
        self.j.restore()
        self.assertEqual(old.read_text(),'old inactive loader');self.assertFalse(new.exists())

    def test_discord_permission_cleanup_preserves_other_and_later_grants(self):
        path=self.put(self.ctx.data/'flatpak/overrides/com.discordapp.Discord','[Context]\nfilesystems=xdg-download;/home/user/.config/Vencord/dist;another-directory;\n[Environment]\nKEEP=yes\n')
        apps.remove_permission_entry(path,'/home/user/.config/Vencord/dist',False)
        self.assertEqual(b.ini_get(path,'[Context]','filesystems'),'xdg-download;another-directory;')
        self.assertEqual(b.ini_get(path,'[Environment]','KEEP'),'yes')

    def test_link_outside_user_scope_is_rejected(self):
        with self.assertRaises(RuntimeError):self.j.link(Path(self.temp.name)/'not-user/link','/tmp/file')

    def test_system_plan_rejects_unrelated_and_escaping_targets(self):
        self.assertTrue(root.permitted(Path('/usr/lib64/qt6/plugins/kwin/effects/plugins/libglass.so')))
        self.assertTrue(root.permitted(Path('/usr/lib64/qt6/plugins/org.kde.kdecoration3/org.kde.kwin.aurorae.v2.so')))
        self.assertTrue(root.permitted(Path('/usr/share/sddm/themes/liquid-glass/Main.qml')))
        for path in ('/etc/passwd','/usr/lib/millennium/../../etc/shadow','/usr/bin/steam','/usr/share/sddm/themes/breeze/Main.qml'):
            self.assertFalse(root.permitted(Path(path)),path)

    def archive(self,members):
        p=self.home/'runtime.tar.gz'
        with tarfile.open(p,'w:gz') as tar:
            for name,data,kind in members:
                member=tarfile.TarInfo(name);member.type=kind
                if kind==tarfile.REGTYPE:member.size=len(data);tar.addfile(member,io.BytesIO(data))
                else:member.linkname='/etc/passwd';tar.addfile(member)
        return p

    def test_runtime_archive_validation_precedes_all_writes(self):
        p=self.archive([('usr/lib/millennium/valid.so',b'good',tarfile.REGTYPE),('usr/lib/millennium/../../../etc/passwd',b'bad',tarfile.REGTYPE)])
        stage=self.home/'stage'
        with self.assertRaises(RuntimeError):full.extract_runtime(p,stage)
        self.assertFalse(stage.exists())

    def test_runtime_archive_rejects_links(self):
        p=self.archive([('usr/lib/millennium/escape',b'',tarfile.SYMTYPE)])
        with self.assertRaises(RuntimeError):full.extract_runtime(p,self.home/'stage')

    def test_flatpak_steam_uses_private_runtime_and_preserves_desktop_exec(self):
        steam=self.home/'.var/app/com.valvesoftware.Steam/.local/share/Steam';steam.mkdir(parents=True)
        original='[Desktop Entry]\nName=Steam\nExec=flatpak run --file-forwarding com.valvesoftware.Steam @@u %U @@\n'
        self.put(self.ctx.system_data[0]/'applications/com.valvesoftware.Steam.desktop',original)
        apps.apply_flatpak_millennium(self.ctx,self.j,steam)
        target=self.ctx.data/'applications/com.valvesoftware.Steam.desktop'
        self.assertIn('MILLENNIUM_RUNTIME_PATH=',target.read_text())
        self.assertIn('@@u %U @@',target.read_text())
        self.assertEqual(str((steam/'ubuntu12_32/libXtst.so.6').readlink()),'../liquid-glass-runtime/libmillennium_bootstrap_x86.so')
        self.assertNotIn('filesystem=',target.read_text())
        self.j.restore();self.assertFalse(target.exists())

    def test_protonplus_native_and_flatpak_gtk4_css_restored(self):
        native=self.put(self.ctx.config/'gtk-4.0/gtk.css','/* user GTK4 */\n')
        flat=self.put(self.home/'.var/app/com.vysp3r.ProtonPlus/config/gtk-4.0/gtk.css','/* user ProtonPlus */\n')
        with patch.object(b,'integrate_apps'):
            apps.install(self.ctx,self.j,False)
        self.assertIn('--window-bg-color',native.read_text())
        self.assertIn('--window-bg-color',flat.read_text())
        self.j.restore()
        self.assertEqual(native.read_text(),'/* user GTK4 */\n')
        self.assertEqual(flat.read_text(),'/* user ProtonPlus */\n')

    def test_teamspeak_stylesheet_selected_without_touching_settings_database(self):
        original='[Desktop Entry]\nName=TeamSpeak 3\nExec=ts3client --keep-this %u\nIcon=teamspeak3\n'
        self.put(self.ctx.system_data[0]/'applications/teamspeak3.desktop',original)
        database=self.put(self.home/'.ts3client/settings.db','keep actual settings database')
        with patch.object(b,'integrate_apps'):apps.install(self.ctx,self.j,False)
        desktop=self.ctx.data/'applications/teamspeak3.desktop'
        self.assertIn('--keep-this %u -stylesheet "',desktop.read_text())
        self.assertEqual(database.read_text(),'keep actual settings database')
        self.j.restore();self.assertFalse(desktop.exists())

    def test_leftover_vencord_download_is_not_mistaken_for_a_patched_client(self):
        self.put(self.ctx.config/'Vencord/dist/patcher.js','downloaded')
        self.put(self.ctx.system_data[0]/'applications/discord.desktop','[Desktop Entry]\nName=Discord\nIcon=discord\nExec=discord\n')
        archive=self.put(self.ctx.data/'discord/resources/app.asar','original Discord archive')
        self.assertTrue(apps.loader_plan(self.ctx)['vencord_needed'])
        archive.write_text('Vencord/dist/patcher.js')
        self.assertFalse(apps.loader_plan(self.ctx)['vencord_needed'])

    def test_failed_native_build_does_not_report_success(self):
        stage=self.home/'stage';stage.mkdir()
        with patch.object(full,'command'),patch.object(full,'kwin_version',return_value='6.8.0'):
            with self.assertRaisesRegex(RuntimeError,'nicht erzeugt'):full.build_native(self.ctx,stage)

    def test_native_build_uses_writable_copies_without_modifying_the_package(self):
        stage=self.home/'native-stage';stage.mkdir()
        original=b.PACKAGE/'vendor/kwin-effects-glass/src/generated/test-marker'
        def build_command(args,**kwargs):
            if '-S' in args:
                source=Path(args[args.index('-S')+1])
                self.assertTrue(source.is_relative_to(self.ctx.state/'build'))
                self.assertFalse(source.is_relative_to(b.PACKAGE))
                self.put(source/'src/generated/test-marker','generated shader')
            if '--install' in args:
                self.put(stage/'usr/lib64/qt6/plugins/kwin/effects/plugins/libglass.so','compiled glass')
        with patch.object(full,'command',side_effect=build_command),patch.object(full,'kwin_version',return_value='6.8.0'):
            self.assertEqual(full.build_native(self.ctx,stage,all_components=True),'6.8.0')
        self.assertFalse(original.exists())
        self.assertTrue((self.ctx.state/'build/kwin-effects-glass-source/src/generated/test-marker').exists())

    def test_native_command_failure_is_reported_with_the_failed_command(self):
        import subprocess
        with patch.object(full.subprocess,'run',side_effect=subprocess.CalledProcessError(9,['cmake'])):
            with self.assertRaisesRegex(RuntimeError,r'Status 9.*cmake.*Installationsprotokoll'):
                full.command(['cmake','--build','path with spaces'])

    def test_compositor_guard_never_loads_an_effect_for_another_running_version(self):
        self.ctx.state.mkdir(parents=True)
        self.put(self.ctx.state/'glass-build.json','{"kwin_version":"6.8.0"}')
        with patch.object(guard.Path,'home',return_value=self.home),patch.dict(guard.os.environ,{'XDG_STATE_HOME':str(self.home/'state')}),patch.object(guard.shutil,'which',return_value='/fake/qdbus'),patch.object(guard,'run',return_value='KWin version: 6.8.1') as run:
            guard.main()
        self.assertTrue((self.ctx.state/'glass-status.txt').exists())
        self.assertFalse(any('glass' in call.args[1:] for call in run.call_args_list))

    def test_xcursor_file_tables_have_real_frames_and_valid_pixel_buffers(self):
        path=TOOLS.parent/'payload/icons/LiquidGlass-Cursors/cursors/wait'
        data=path.read_bytes();magic,header,version,count=struct.unpack_from('<4I',data)
        self.assertEqual(magic,0x72756358);self.assertEqual(header,16);self.assertEqual(count,60)
        for i in range(count):
            type_,size,offset=struct.unpack_from('<3I',data,16+i*12)
            chunk=struct.unpack_from('<9I',data,offset)
            self.assertEqual(type_,0xfffd0002);self.assertEqual(chunk[1],type_)
            self.assertEqual(chunk[4],size);self.assertEqual(chunk[5],size)
            self.assertLess(chunk[6],size);self.assertLess(chunk[7],size)
            self.assertLessEqual(offset+36+size*size*4,len(data))


if __name__=='__main__':unittest.main()
