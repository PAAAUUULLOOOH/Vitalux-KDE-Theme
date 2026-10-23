#!/usr/bin/env python3
"""User-local install with a reversible, per-key settings journal. MIT license."""
from __future__ import annotations
import argparse
import base64
import configparser
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parent.parent
VERSION = json.loads((PACKAGE / "design/vitalux.json").read_text())["version"]
GLOBAL_ID = "io.github.PAAAUUULLOOOH.LiquidGlass"
BEGIN = "/* BEGIN LIQUID-GLASS-KDE */"
END = "/* END LIQUID-GLASS-KDE */"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)
NAMED_APPS = {
    "Firefox": ("firefox", "org.mozilla.firefox", "firefox-esr"),
    "Discord": ("discord", "com.discordapp.Discord"),
    "Steam": ("steam", "com.valvesoftware.Steam"),
    "TeamSpeak 3": ("teamspeak3", "teamspeak", "ts3client_linux_amd64", "com.teamspeak.TeamSpeak"),
    "ProtonPlus": ("com.vysp3r.ProtonPlus", "protonplus"),
    "Haruna": ("haruna", "org.kde.haruna"),
}


def atomic_write(path: Path, value: bytes, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise RuntimeError(f"Symlink wird nicht überschrieben: {path}")
    fd, name = tempfile.mkstemp(prefix=".liquid-glass-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def read_ini(path):
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    try:
        c.read(path, encoding="utf-8")
    except (configparser.Error, UnicodeError):
        pass
    return c


def ini_get(path, group, key):
    current = ""
    value = None
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("["):
            current = line.strip()
        elif current == group and "=" in line and not line.lstrip().startswith(("#", ";")):
            k, v = line.split("=", 1)
            if k.strip() == key:
                value = v
    return value


def ini_set(path, group, key, value):
    """Change just the owned key, preserving unrelated sections and comments."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines(keepends=True)
    current, found_group, inserted = "", group == "", False
    out = []
    for line in lines:
        if line.strip().startswith("["):
            if current == group and not inserted:
                if value is not None:
                    out.append(f"{key}={value}\n")
                inserted = True
            current = line.strip()
            found_group |= current == group
        if current == group and "=" in line and not line.lstrip().startswith(("#", ";")) and line.split("=", 1)[0].strip() == key:
            if not inserted and value is not None:
                out.append(f"{key}={value}\n")
            inserted = True
        else:
            out.append(line)
    if not inserted and found_group:
        if value is not None:
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.append(f"{key}={value}\n")
    elif not inserted and value is not None:
        if out and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.extend([f"\n{group}\n", f"{key}={value}\n"])
    atomic_write(path, "".join(out).encode(), path.stat().st_mode & 0o777 if path.exists() else 0o600)


@dataclass
class Context:
    home: Path
    data: Path
    config: Path
    state: Path
    system_data: tuple[Path, ...]

    @classmethod
    def current(cls):
        home = Path.home()
        paths = lambda key, default: Path(os.environ.get(key, str(default)))
        return cls(home, paths("XDG_DATA_HOME", home / ".local/share"), paths("XDG_CONFIG_HOME", home / ".config"), paths("XDG_STATE_HOME", home / ".local/state") / "liquid-glass-kde", tuple(Path(p) for p in os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if p))

    def allowed(self, path):
        # Firefox profiles may live elsewhere under the user's home. Never follow
        # a profile/managed file symlink out of the authorized user directories.
        roots = (self.home.resolve(), self.data.resolve(), self.config.resolve(), self.state.resolve())
        return any(path.resolve().is_relative_to(root) for root in roots)


class Journal:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.state / "install.json"
        self.doc = json.loads(self.path.read_text()) if self.path.exists() else {"schema": 1, "version": VERSION, "generation": uuid.uuid4().hex, "files": {}, "keys": {}, "blocks": {}, "desktop": None}
        self.doc.setdefault("json", {})
        self.doc.setdefault("links", {})

    def save(self):
        atomic_write(self.path, (json.dumps(self.doc, ensure_ascii=False, indent=2) + "\n").encode(), 0o600)

    def check(self, path):
        if not self.ctx.allowed(path) or path.is_symlink():
            raise RuntimeError(f"Unsicherer Zielpfad: {path}")

    def backup(self, path):
        key = self.doc["generation"] + "/" + hashlib.sha256(str(path).encode()).hexdigest()
        dest = self.ctx.state / "backups" / key
        if path.exists() and not dest.exists():
            atomic_write(dest, path.read_bytes(), 0o600)
        return key if dest.exists() else None

    def put(self, path, data, mode=0o644):
        self.check(path)
        key = str(path)
        if key not in self.doc["files"]:
            self.doc["files"][key] = {"backup": self.backup(path), "mode": path.stat().st_mode & 0o777 if path.exists() else mode, "installed": None}
        # Record the intended content before replacing the file so an interrupted
        # install can still be removed using its already-saved journal.
        self.doc["files"][key]["installed"] = hashlib.sha256(data).hexdigest()
        self.save()
        atomic_write(path, data, mode)
        self.doc["files"][key]["installed"] = digest(path)
        self.save()

    def set(self, path, group, key, value):
        self.check(path)
        ident = json.dumps([str(path), group, key])
        if ident not in self.doc["keys"]:
            self.doc["keys"][ident] = {"old": ini_get(path, group, key), "installed": value, "file_existed": path.exists()}
            self.backup(path)
            self.save()
        ini_set(path, group, key, value)
        self.doc["keys"][ident]["installed"] = value
        self.save()

    def block(self, path, content):
        self.check(path)
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        pattern = re.compile(r"\n?" + re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
        block = BEGIN + "\n" + content.strip() + "\n" + END
        if str(path) not in self.doc["blocks"]:
            self.doc["blocks"][str(path)] = {"backup": self.backup(path), "existed": path.exists(), "mode": path.stat().st_mode & 0o777 if path.exists() else 0o600, "installed": block}
            self.save()
        text = pattern.sub("\n", text).rstrip("\n") + "\n" + block + "\n"
        atomic_write(path, text.encode(), 0o600)
        self.doc["blocks"][str(path)]["installed"] = block
        self.doc["blocks"][str(path)]["installed_file"] = digest(path)
        self.save()

    def json_set(self, path, pointer, value):
        self.check(path)
        data = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(data, dict):
            raise ValueError(f"JSON-Konfiguration ist kein Objekt: {path}")
        cursor = data
        exists = True
        for part in pointer[:-1]:
            if part not in cursor:
                exists = False
                cursor[part] = {}
            if not isinstance(cursor[part], dict):
                raise ValueError(f"JSON-Einstellung hat einen inkompatiblen Typ: {path} / {part}")
            cursor = cursor[part]
        exists = exists and pointer[-1] in cursor
        ident = json.dumps([str(path), list(pointer)])
        if ident not in self.doc["json"]:
            self.doc["json"][ident] = {"exists": exists, "old": cursor.get(pointer[-1]), "installed": value, "file_existed": path.exists()}
            self.backup(path)
        self.doc["json"][ident]["installed"] = value
        self.save()
        cursor[pointer[-1]] = value
        atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2)+"\n").encode(), 0o600)

    def link(self, path, target):
        if not self.ctx.allowed(path.parent):
            raise RuntimeError(f"Unsicherer Link-Zielordner: {path.parent}")
        ident = str(path)
        if ident not in self.doc["links"]:
            if path.is_symlink():
                original = {"kind": "link", "target": os.readlink(path)}
            elif path.is_file():
                original = {"kind": "file", "backup": self.backup(path), "mode": path.stat().st_mode & 0o777}
            elif path.exists():
                raise RuntimeError(f"Ziel ist keine Datei: {path}")
            else:
                original = {"kind": "absent"}
            self.doc["links"][ident] = {"old": original, "installed": str(target)}
        self.doc["links"][ident]["installed"] = str(target)
        self.save()
        path.parent.mkdir(parents=True, exist_ok=True)
        staging = path.parent / (".liquid-glass-link-" + uuid.uuid4().hex)
        try:
            staging.symlink_to(target)
            os.replace(staging, path)
        finally:
            staging.unlink(missing_ok=True)

    def restore(self):
        kept = []
        for ident, item in reversed(list(self.doc["json"].items())):
            p, pointer = json.loads(ident)
            path = Path(p)
            self.check(path)
            if not path.exists():
                continue
            data = json.loads(path.read_text())
            cursor = data
            parents = []
            for part in pointer[:-1]:
                if not isinstance(cursor, dict) or not isinstance(cursor.get(part), dict):
                    cursor = None
                    break
                parents.append((cursor,part)); cursor = cursor[part]
            if cursor is None or cursor.get(pointer[-1]) != item["installed"]:
                kept.append(p+" / "+"/".join(pointer))
                continue
            if item["exists"]:
                cursor[pointer[-1]] = item["old"]
            else:
                cursor.pop(pointer[-1], None)
                for parent,part in reversed(parents):
                    if not parent[part]:parent.pop(part)
            if not data and not item["file_existed"]:
                path.unlink()
            else:
                atomic_write(path,(json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode(),0o600)
        for p,item in reversed(list(self.doc["links"].items())):
            path=Path(p)
            if not self.ctx.allowed(path.parent):
                raise RuntimeError(f"Unsicherer Link-Zielordner: {path.parent}")
            if path.is_symlink() and os.readlink(path)==item["installed"]:
                path.unlink()
                old=item["old"]
                if old["kind"]=="link":path.symlink_to(old["target"])
                elif old["kind"]=="file":atomic_write(path,(self.ctx.state/"backups"/old["backup"]).read_bytes(),old["mode"])
            elif path.exists() or path.is_symlink():kept.append(p)
        for ident, item in reversed(list(self.doc["keys"].items())):
            p, group, key = json.loads(ident)
            path = Path(p)
            self.check(path)
            if ini_get(path, group, key) == item["installed"]:
                ini_set(path, group, key, item["old"])
                # Remove an originally absent config if only empty section headers remain.
                if not item["file_existed"] and not any("=" in s and not s.lstrip().startswith(("#", ";")) for s in path.read_text().splitlines()):
                    path.unlink(missing_ok=True)
            else:
                kept.append(p + " / " + key)
        for p, item in reversed(list(self.doc["blocks"].items())):
            path = Path(p)
            self.check(path)
            if path.exists():
                if digest(path) == item.get("installed_file"):
                    if item["backup"]:
                        atomic_write(path, (self.ctx.state / "backups" / item["backup"]).read_bytes(), item.get("mode", 0o600))
                    else:
                        path.unlink()
                    continue
                text = path.read_text(encoding="utf-8")
                if item["installed"] in text:
                    text = text.replace(item["installed"], "", 1)
                    if not text.strip() and not item["existed"]:
                        path.unlink()
                    else:
                        atomic_write(path, text.encode(), 0o600)
                else:
                    kept.append(p)
        for p, item in reversed(list(self.doc["files"].items())):
            path = Path(p)
            self.check(path)
            if not path.exists() or digest(path) == item["installed"]:
                if item["backup"]:
                    atomic_write(path, (self.ctx.state / "backups" / item["backup"]).read_bytes(), item["mode"])
                else:
                    path.unlink(missing_ok=True)
                # Only remove empty package-created leaf directories.
                parent = path.parent
                while parent not in (self.ctx.data, self.ctx.config, self.ctx.home):
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent
            else:
                kept.append(p)
        return kept


@contextmanager
def install_lock(ctx):
    ctx.state.mkdir(parents=True, exist_ok=True)
    with (ctx.state / "install.lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def run(args, timeout=30):
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=True).stdout.strip()


def dbus_program():
    for name in ("qdbus6", "qdbus-qt6", "qdbus"):
        if shutil.which(name):
            return shutil.which(name)
    for p in ("/usr/lib64/qt6/bin/qdbus", "/usr/lib/qt6/bin/qdbus"):
        if Path(p).is_file():
            return p
    return None


def plasma_script(script):
    dbus = dbus_program()
    if not dbus:
        raise RuntimeError("Qt6-qdbus fehlt; Theme ist über KDE-Systemeinstellungen auswählbar.")
    return run([dbus, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script])


SNAPSHOT = '''var result={launchers:[],desktops:[]};
var containers=panels().concat(desktops());
for(var i=0;i<containers.length;i++){
 var c=containers[i];var widgets=c.widgets();
 for(var j=0;j<widgets.length;j++){
  var w=widgets[j];
  if(["org.kde.plasma.kickoff","org.kde.plasma.kicker","org.kde.plasma.kickerdash"].indexOf(w.type)>=0){
   w.currentConfigGroup=["General"];
   result.launchers.push({container:c.id,id:w.id,icon:w.readConfig("icon","")});
  }
 }
}
var ds=desktops();for(var i=0;i<ds.length;i++){
 var d=ds[i];d.currentConfigGroup=["Wallpaper","org.kde.image","General"];
 result.desktops.push({id:d.id,plugin:d.wallpaperPlugin,image:d.readConfig("Image","")});
}
print(JSON.stringify(result));'''


def desktop_snapshot():
    text = plasma_script(SNAPSHOT)
    for line in reversed(text.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError("Plasma hat keine lesbare Desktop-Konfiguration zurückgegeben.")


def change_desktop(snapshot, wallpaper, restore=False):
    body = '''var state=__LG_STATE__; var restoring=__LG_RESTORE__;var image=__LG_IMAGE__;
var containers=panels().concat(desktops());
for(var i=0;i<containers.length;i++){
 var c=containers[i];var ws=c.widgets();
 for(var j=0;j<ws.length;j++)for(var k=0;k<state.launchers.length;k++){
  var old=state.launchers[k],w=ws[j];if(w.id!==old.id||c.id!==old.container)continue;
  w.currentConfigGroup=["General"];
  if(!restoring||w.readConfig("icon","")==="liquidglass-opensuse")w.writeConfig("icon",restoring?old.icon:"liquidglass-opensuse");
 }
}
var ds=desktops();for(var i=0;i<ds.length;i++)for(var j=0;j<state.desktops.length;j++){
 var d=ds[i],old=state.desktops[j];if(d.id!==old.id)continue;
 d.currentConfigGroup=["Wallpaper","org.kde.image","General"];
 if(restoring){if(d.wallpaperPlugin==="org.kde.image"&&d.readConfig("Image","")===image){d.writeConfig("Image",old.image);d.wallpaperPlugin=old.plugin;}}
 else{d.wallpaperPlugin="org.kde.image";d.currentConfigGroup=["Wallpaper","org.kde.image","General"];d.writeConfig("Image",image);}
}'''
    # JSON handles all path/string escaping; no shell interpolation is used.
    values = {"__LG_STATE__": json.dumps(snapshot), "__LG_RESTORE__": "true" if restore else "false", "__LG_IMAGE__": json.dumps(wallpaper)}
    body = re.sub(r"__LG_(?:STATE|RESTORE|IMAGE)__", lambda match: values[match[0]], body)
    plasma_script(body)


def refresh_desktop():
    for cmd in ("kbuildsycoca6", "gtk-update-icon-cache"):
        if shutil.which(cmd) and cmd == "kbuildsycoca6":
            try:
                run([cmd, "--noincremental"], timeout=60)
            except (subprocess.SubprocessError, OSError):
                pass
    dbus = dbus_program()
    if dbus:
        for args in [("org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"), ("org.kde.KGlobalSettings", "/KGlobalSettings", "org.kde.KGlobalSettings.notifyChange", "0", "0")]:
            try:
                run([dbus, *args])
            except (subprocess.SubprocessError, OSError):
                pass


def desktop_entries(ctx):
    roots = (ctx.data, ctx.home / ".local/share/flatpak/exports/share", Path("/var/lib/flatpak/exports/share"), *ctx.system_data)
    seen = set()
    for root in roots:
        folder = root / "applications"
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*.desktop")):
            ident = str(path.relative_to(folder)).replace("/", "-")
            if ident in seen:
                continue
            seen.add(ident)
            c = read_ini(path)
            if "Desktop Entry" not in c:
                continue
            d = c["Desktop Entry"]
            if d.get("Hidden", "false") == "true" or d.get("NoDisplay", "false") == "true" or d.get("Type", "Application") != "Application":
                continue
            yield path, ident, d.get("Name", path.stem), d.get("Icon", "")


class IconFinder:
    def __init__(self, ctx):
        current = ini_get(ctx.config / "kdeglobals", "[Icons]", "Theme") or "breeze"
        themes = [current, "hicolor", "breeze", "Adwaita"]
        roots = (ctx.data / "icons", ctx.home / ".icons", ctx.home / ".local/share/flatpak/exports/share/icons", Path("/var/lib/flatpak/exports/share/icons"), *(p / "icons" for p in ctx.system_data))
        self.files = {}
        # Only app/places icons; symbolic controls deliberately inherit Breeze.
        for theme in dict.fromkeys(themes):
            if theme == "LiquidGlass":
                continue
            for root in roots:
                folder = root / theme
                if not folder.exists():
                    continue
                candidates = [p for p in folder.rglob("*") if p.suffix.lower() in (".svg", ".svgz", ".png") and any(s.lower() in ("apps", "applications", "places", "distributors", "distributor") for s in p.parts)]
                def rank(p):
                    return (0 if p.suffix in (".svg", ".svgz") else 1, -max([int(s) for part in p.parts for s in re.findall(r"(?<!\d)(\d{2,3})(?!\d)", part)] or [0]), str(p))
                for p in sorted(candidates, key=rank):
                    self.files.setdefault(p.stem, p)
        for root in ctx.system_data:
            for folder in (root / "pixmaps", root / "pixmaps/distribution-logos"):
                if folder.exists():
                    for p in folder.glob("*"):
                        if p.suffix.lower() in (".svg", ".svgz", ".png"):
                            self.files.setdefault(p.stem, p)

    def find(self, name):
        p = Path(name)
        if p.is_absolute() and p.is_file():
            return p
        return self.files.get(name) or self.files.get(p.stem)


def design_reference():
    """Use the same pinned source palette as the generated desktop surfaces."""
    document = json.loads((PACKAGE / "design/vitalux.json").read_text())
    required = ("bg", "sidebar", "card", "border", "text", "muted", "accent", "secondary")
    for role in required:
        if not re.fullmatch(r"#[\da-fA-F]{6}", document["colors"].get(role, "")):
            raise ValueError("Ungültige Vitalux-Originalfarbe: " + role)
    return document


def glass_icon(source):
    """Preserve the installed app's own mark on an original glass plate."""
    root = ET.Element(f"{{{SVG_NS}}}svg", {"width": "128", "height": "128", "viewBox": "0 0 128 128"})
    reference = design_reference()
    colors = reference['colors']
    defs = ET.Element(f"{{{SVG_NS}}}defs")
    for ident, stops in [('lg-plate', reference['material']['wash']), ('lg-rim', reference['material']['edge'])]:
        gradient = ET.SubElement(defs, f"{{{SVG_NS}}}linearGradient", {'id': ident, 'x2': '.8', 'y2': '1'})
        for position, role, alpha in stops:
            ET.SubElement(gradient, f"{{{SVG_NS}}}stop", {'offset': str(position), 'stop-color': colors[role], 'stop-opacity': str(alpha / 255)})
    root.append(defs)
    for x, y, w, h, r, fill, opacity in [(8, 10, 112, 112, 25, colors['bg'], ".35"), (8, 8, 112, 112, 25, "url(#lg-plate)", "1")]:
        a = {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "rx": str(r), "fill": fill, "opacity": opacity}
        if y == 8:
            a.update({"stroke": "url(#lg-rim)", "stroke-width": "1.5"})
        ET.SubElement(root, f"{{{SVG_NS}}}rect", a)
    if source.suffix.lower() in (".svg", ".svgz"):
        data = gzip.decompress(source.read_bytes()) if source.suffix.lower() == ".svgz" else source.read_bytes()
        if len(data) > 4_000_000 or b"<!ENTITY" in data.upper():
            raise ValueError("Ungültige oder zu große SVG")
        original = ET.fromstring(data)
        if original.tag != f"{{{SVG_NS}}}svg":
            raise ValueError("Keine SVG-Grafik")
        # Prefix source IDs and references to avoid collisions with the glass plate.
        ids = {el.get("id"): "app-" + el.get("id") for el in original.iter() if el.get("id")}
        for el in original.iter():
            if el.tag.endswith(("script", "foreignObject")):
                raise ValueError("Aktive SVG-Inhalte werden nicht übernommen")
            for key, value in list(el.attrib.items()):
                if key == "id":
                    value = ids[value]
                else:
                    value = re.sub(r"url\(#([^)]*)\)", lambda m: f'url(#{ids.get(m[1], m[1])})', value)
                    if key.endswith("href") and value.startswith("#"):
                        value = "#" + ids.get(value[1:], value[1:])
                    elif key.endswith("href") and not value.startswith("data:"):
                        raise ValueError("Externe SVG-Referenz wird nicht übernommen")
                el.set(key, value)
            if el.tag.endswith("style") and el.text:
                for old, new in ids.items():
                    el.text = re.sub(r"#" + re.escape(old) + r"(?![\w-])", "#" + new, el.text)
        if not original.get("viewBox"):
            w = re.match(r"[\d.]+", original.get("width", "128"))
            h = re.match(r"[\d.]+", original.get("height", "128"))
            original.set("viewBox", f'0 0 {w[0] if w else 128} {h[0] if h else 128}')
        bounds = [float(v) for v in re.split(r"[\s,]+", original.get("viewBox").strip())]
        if len(bounds) != 4 or bounds[2] <= 0 or bounds[3] <= 0:
            raise ValueError("Ungültiger SVG-Ansichtsbereich")
        vx, vy, vw, vh = bounds
        factor = min(78 / vw, 78 / vh)
        tx = 25 + (78 - vw*factor)/2 - vx*factor
        ty = 25 + (78 - vh*factor)/2 - vy*factor
        # QtSvg/KSvg's SVG Tiny renderer skips nested <svg> viewports. Flatten
        # the original root to groups while preserving its viewBox transform.
        viewport = ET.SubElement(root, f"{{{SVG_NS}}}g", {"transform": f"translate({tx:g} {ty:g}) scale({factor:g})"})
        attrs = {k:v for k,v in original.attrib.items() if k not in ("viewBox", "width", "height", "x", "y", "preserveAspectRatio", "version")}
        group = ET.SubElement(viewport, f"{{{SVG_NS}}}g", attrs)
        for child in list(original):
            group.append(child)
    else:
        if source.suffix.lower() != ".png":
            raise ValueError("Nur SVG, SVGZ und PNG können als Original-Icon übernommen werden")
        b = source.read_bytes()
        if len(b) > 4_000_000 or not b.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Icon ist zu groß")
        ET.SubElement(root, f"{{{SVG_NS}}}image", {"x": "25", "y": "25", "width": "78", "height": "78", "preserveAspectRatio": "xMidYMid meet", f"{{{XLINK_NS}}}href": "data:image/png;base64," + base64.b64encode(b).decode()})
    ET.SubElement(root, f"{{{SVG_NS}}}path", {"d": "M22 28Q25 16 42 16H85", "fill": "none", "stroke": colors['secondary'], "stroke-width": "1", "stroke-opacity": ".48", "stroke-linecap": "round"})
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def generate_icons(ctx, journal, overrides=True):
    finder = IconFinder(ctx)
    done = set()
    entries = list(desktop_entries(ctx))
    # Active launcher is the best source on a branded openSUSE desktop.
    names = ["distributor-logo-opensuse", "distributor-logo", "start-here-branding", "opensuse", "geeko-color", "square-hicolor"]
    logo = None
    try:
        os_release=Path('/etc/os-release').read_text()
        logo=re.search(r'^LOGO=["\']?([^"\'\n]+)',os_release,re.M)
        if logo:names.insert(0,logo[1])
    except OSError:pass
    names.extend(['distributor-logo-Tumbleweed','start-here-opensuse'])
    if journal.doc.get("desktop"):
        names = [x["icon"] for x in journal.doc["desktop"]["launchers"] if x["icon"] and x["icon"] != "liquidglass-opensuse"] + names
    launcher = next((finder.find(n) for n in names if finder.find(n)), None)
    if launcher:
        data = glass_icon(launcher)
        aliases=["liquidglass-opensuse", "start-here-branding", "distributor-logo-opensuse"]
        if logo and re.fullmatch(r'[\w.+-]+',logo[1]):aliases.append(logo[1])
        for name in dict.fromkeys(aliases):
            journal.put(ctx.data / f"icons/LiquidGlass/scalable/places/{name}.svg", data)
    else:
        print("Hinweis: Kein installiertes openSUSE-Logo gefunden. Der vorhandene Starter bleibt unverändert.")
    for path, ident, display_name, name in entries:
        if not name:
            continue
        source = finder.find(name)
        if not source:
            continue
        target_name = name if re.fullmatch(r"[\w.+-]+", name) else "liquidglass-" + re.sub(r"[^\w.+-]", "-", ident.removesuffix(".desktop"))
        if target_name in done:
            continue
        try:
            data = glass_icon(source)
        except (ET.ParseError, ValueError, OSError) as e:
            print(f"Icon bleibt original ({display_name}): {e}")
            continue
        journal.put(ctx.data / f"icons/LiquidGlass/scalable/apps/{target_name}.svg", data)
        done.add(target_name)
        if overrides and Path(name).is_absolute():
            # A user-local desktop override changes only Icon; Exec/permissions stay intact.
            text = path.read_text(encoding="utf-8")
            group, out = "", []
            for line in text.splitlines(keepends=True):
                if line.strip().startswith("["):
                    group = line.strip()
                if group == "[Desktop Entry]" and line.startswith("Icon="):
                    line = f"Icon={target_name}\n"
                out.append(line)
            journal.put(ctx.data / "applications" / ident, "".join(out).encode())
    reports = {}
    for label, aliases in NAMED_APPS.items():
        source = next((finder.find(n) for n in aliases if finder.find(n)), None)
        if source:
            try:
                data = glass_icon(source)
                for alias in aliases:
                    if alias not in done:
                        journal.put(ctx.data / f"icons/LiquidGlass/scalable/apps/{alias}.svg", data)
                reports[label] = "Original-Icon auf Glasplatte"
            except (ET.ParseError, ValueError, OSError):
                reports[label] = "Original-Icon beibehalten"
        else:
            reports[label] = "Nicht gefunden; nach Installation der App install.sh erneut ausführen"
    journal.doc["app_icons"] = reports
    journal.doc["launcher_available"] = bool(launcher)
    journal.save()
    print(f"{len(done)} installierte App-Icons angepasst.")
    for name, result in reports.items():
        print(f"  {name}: {result}")


def firefox_profiles(ctx):
    roots = (ctx.home / ".mozilla/firefox", ctx.home / ".config/mozilla/firefox", ctx.home / ".var/app/org.mozilla.firefox/.mozilla/firefox", ctx.home / ".var/app/org.mozilla.firefox/.config/mozilla/firefox")
    seen = set()
    for root in roots:
        c = read_ini(root / "profiles.ini")
        for section in c.sections():
            if not section.startswith("Profile") or not c[section].get("Path"):
                continue
            raw = c[section]["Path"]
            path = root / raw if c[section].get("IsRelative", "1") == "1" else Path(raw)
            path = path.resolve()
            if path.is_dir() and ctx.allowed(path) and path not in seen:
                seen.add(path)
                yield path


def integrate_apps(ctx, journal, firefox=True):
    if firefox:
        css = (PACKAGE / "integrations/firefox/userChrome.css").read_text()
        profiles = list(firefox_profiles(ctx))
        for profile in profiles:
            journal.block(profile / "chrome/userChrome.css", css)
            journal.block(profile / "user.js", 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);')
        print(f"Firefox: {len(profiles)} vorhandene Profile vorbereitet; wird beim nächsten Firefox-Start aktiv.")
    ts = ctx.home / ".ts3client/styles"
    if ts.parent.exists():
        journal.put(ts / "LiquidGlass.qss", (PACKAGE / "integrations/teamspeak3/LiquidGlass.qss").read_bytes())


def plugin_paths():
    return tuple(Path(p) for p in ("/usr/lib64/qt6/plugins", "/usr/lib/qt6/plugins", "/usr/lib/x86_64-linux-gnu/qt6/plugins", "/usr/lib64/qt5/plugins", "/usr/lib/x86_64-linux-gnu/qt5/plugins"))


def has_kvantum():
    return any((p / "styles/libkvantum.so").is_file() for p in plugin_paths() if "qt5" not in str(p))


def aurorae_plugin():
    for name in ("org.kde.kwin.aurorae.v2", "org.kde.kwin.aurorae"):
        if any((p / f"org.kde.kdecoration3/{name}.so").is_file() or (p / f"org.kde.kdecoration2/{name}.so").is_file() for p in plugin_paths()):
            return name
    return None


def apply_settings(ctx, journal):
    scheme = read_ini(PACKAGE / "payload/color-schemes/LiquidGlass.colors")
    accent = design_reference()['colors']['accent']
    accent_rgb = ','.join(str(int(accent[i:i+2], 16)) for i in (1, 3, 5))
    for section in scheme.sections():
        if section == "General":
            continue
        for key, value in scheme[section].items():
            journal.set(ctx.config / "kdeglobals", f"[{section}]", key, value)
    for group, key, value in [("[KDE]", "LookAndFeelPackage", GLOBAL_ID), ("[General]", "ColorScheme", "LiquidGlass"), ("[General]", "AccentColor", accent_rgb), ("[Icons]", "Theme", "LiquidGlass"), ("[KDE]", "widgetStyle", "kvantum" if has_kvantum() else "Breeze")]:
        journal.set(ctx.config / "kdeglobals", group, key, value)
    journal.set(ctx.config / "plasmarc", "[Theme]", "name", "liquid-glass")
    journal.set(ctx.config / "Kvantum/kvantum.kvconfig", "", "theme", "KvLiquidGlass")
    for key in ("blurEnabled", "contrastEnabled"):
        journal.set(ctx.config / "kwinrc", "[Plugins]", key, "true")
    plugin = aurorae_plugin()
    if plugin:
        journal.set(ctx.config / "kwinrc", "[org.kde.kdecoration2]", "library", plugin)
        journal.set(ctx.config / "kwinrc", "[org.kde.kdecoration2]", "theme", "__aurorae__svg__liquid-glass")
    else:
        print("Aurorae nicht gefunden: Deine bisherige Fensterdekoration bleibt aktiv. Siehe ANLEITUNG.md.")
    for key, value in [("gtk-theme-name", "LiquidGlass"), ("gtk-icon-theme-name", "LiquidGlass"), ("gtk-application-prefer-dark-theme", "true")]:
        journal.set(ctx.config / "gtk-3.0/settings.ini", "[Settings]", key, value)
    # kde-gtk-config reads the name from kdeglobals on subsequent login.
    journal.set(ctx.config / "kdeglobals", "[KDE]", "gtkTheme", "LiquidGlass")
    journal.set(ctx.config / "kcminputrc", "[Mouse]", "cursorTheme", "LiquidGlass-Cursors")
    journal.set(ctx.config / "ksplashrc", "[KSplash]", "Theme", GLOBAL_ID)
    wallpaper = (ctx.data / "wallpapers/LiquidGlass/contents/images/3840x2160.jpg").as_uri()
    journal.set(ctx.config / "kscreenlockerrc", "[Greeter]", "WallpaperPlugin", "org.kde.image")
    journal.set(ctx.config / "kscreenlockerrc", "[Greeter][Wallpaper][org.kde.image][General]", "Image", wallpaper)
    if not has_kvantum():
        print("Kvantum Qt6 fehlt: KDE-Apps verwenden vorerst Breeze mit der Liquid-Glass-Palette.")
        print("Für die eigenen Glas-Steuerelemente Kvantum Qt6 nachinstallieren und install.sh erneut starten.")


def verify_package():
    manifest = json.loads((PACKAGE / "SHA256SUMS.json").read_text())
    for rel, expected in manifest.items():
        path = PACKAGE / rel
        if not path.resolve().is_relative_to(PACKAGE) or not path.is_file() or digest(path) != expected:
            raise RuntimeError(f"ZIP-Inhalt fehlt oder wurde verändert: {rel}. Bitte erneut entpacken.")


def install(ctx, only=False, firefox=True):
    journal = Journal(ctx)
    # Get the desktop state before choosing the branded launcher source.
    live = False
    if not only and shutil.which("plasmashell"):
        try:
            snapshot = desktop_snapshot()
            live = True
            if journal.doc["desktop"] is None:
                journal.doc["desktop"] = snapshot
                journal.save()
        except (RuntimeError, subprocess.SubprocessError, OSError) as e:
            print(f"Desktop gerade nicht erreichbar: {e}")
    for path in sorted((PACKAGE / "payload").rglob("*")):
        if path.is_file():
            journal.put(ctx.data / path.relative_to(PACKAGE / "payload"), path.read_bytes())
    for path in sorted((PACKAGE / "kvantum").rglob("*")):
        if path.is_file():
            journal.put(ctx.config / "Kvantum" / path.relative_to(PACKAGE / "kvantum"), path.read_bytes())
    for path in sorted((PACKAGE / "gtk").rglob("*")):
        if path.is_file():
            journal.put(ctx.data / "themes/LiquidGlass" / path.relative_to(PACKAGE / "gtk"), path.read_bytes())
    # The selectable global package should use only plugins actually installed
    # on this desktop, including the new Aurorae v2 implementation in Plasma 6.8.
    defaults = (PACKAGE / "payload" / f"plasma/look-and-feel/{GLOBAL_ID}/contents/defaults").read_text()
    if has_kvantum():
        defaults = defaults.replace("widgetStyle=Breeze", "widgetStyle=kvantum")
    plugin = aurorae_plugin()
    if not plugin:
        defaults = defaults.replace("library=org.kde.kwin.aurorae.v2", "library=org.kde.breeze").replace("theme=__aurorae__svg__liquid-glass", "theme=Breeze")
    else:
        defaults = defaults.replace("library=org.kde.kwin.aurorae.v2", "library=" + plugin)
    journal.put(ctx.data / f"plasma/look-and-feel/{GLOBAL_ID}/contents/defaults", defaults.encode())
    generate_icons(ctx, journal, overrides=not only)
    if not only:
        integrate_apps(ctx, journal, firefox)
        apply_settings(ctx, journal)
        image = (ctx.data / "wallpapers/LiquidGlass/contents/images/3840x2160.jpg").as_uri()
        journal.doc["wallpaper"] = image
        journal.save()
        if live:
            snap = dict(journal.doc["desktop"])
            if not journal.doc.get("launcher_available"):
                snap["launchers"] = []
            try:
                change_desktop(snap, image)
            except (RuntimeError, subprocess.SubprocessError, OSError) as e:
                print(f"Hintergrund/Starter bitte in KDE auswählen: {e}")
        refresh_desktop()
    print("\nLiquid Glass ist installiert." if not only else "\nLiquid Glass ist installiert, aber noch nicht angewendet.")
    print("KDE-Systemeinstellungen → Farben & Designs → Globales Design → Liquid Glass · openSUSE")
    print("Einmal ab- und anmelden, damit alle laufenden Apps die neuen Einstellungen übernehmen.")
    print(f"Sicherung und Status: {ctx.state}")
    print("Rückgängig: bash uninstall.sh")


def uninstall(ctx):
    journal = Journal(ctx)
    if not journal.path.exists():
        print("Keine Installation für diesen Benutzer gefunden.")
        return
    if journal.doc.get("desktop"):
        try:
            change_desktop(journal.doc["desktop"], journal.doc.get("wallpaper", ""), restore=True)
        except (RuntimeError, subprocess.SubprocessError, OSError):
            print("Plasma nicht erreichbar. Starter/Hintergrund werden beim nächsten Anmelden wiederhergestellt.")
            # Apply the exact owned image/icon keys to Plasma's persistent config,
            # but preserve any manually chosen new wallpaper or launcher.
        plasma = ctx.config / "plasma-org.kde.plasma.desktop-appletsrc"
        for w in journal.doc["desktop"]["launchers"]:
            group = f'[Containments][{w["container"]}][Applets][{w["id"]}][Configuration][General]'
            if ini_get(plasma, group, "icon") == "liquidglass-opensuse":
                ini_set(plasma, group, "icon", w["icon"] or None)
        for d in journal.doc["desktop"]["desktops"]:
            group = f'[Containments][{d["id"]}][Wallpaper][org.kde.image][General]'
            if ini_get(plasma, group, "Image") == journal.doc.get("wallpaper"):
                ini_set(plasma, group, "Image", d["image"] or None)
                ini_set(plasma, f'[Containments][{d["id"]}]', "wallpaperplugin", d["plugin"])
    kept = journal.restore()
    refresh_desktop()
    # Keep original backups for recovery even when some post-install edits remain.
    archive = ctx.state / "last-uninstall.json"
    atomic_write(archive, journal.path.read_bytes(), 0o600)
    journal.path.unlink()
    print("Liquid Glass deinstalliert. Vorherige Einstellungen wiederhergestellt.")
    if kept:
        print("Nachträglich geänderte Dateien/Einstellungen wurden beibehalten:")
        for p in kept:
            print("  " + p)
    print("Bitte einmal ab- und anmelden; Firefox und TeamSpeak ebenfalls neu öffnen.")


def main():
    p = argparse.ArgumentParser(description="Liquid Glass für openSUSE / Plasma 6.8")
    p.add_argument("action", choices=("install", "uninstall"))
    p.add_argument("--install-only", action="store_true", help="Nur Assets installieren, keine Einstellungen ändern")
    p.add_argument("--no-firefox", action="store_true", help="Vorhandene Firefox-Profile nicht anpassen")
    p.add_argument("--check", action="store_true", help="Paket und Voraussetzungen prüfen, nichts installieren")
    args = p.parse_args()
    if os.geteuid() == 0:
        p.error("Bitte als normaler Benutzer starten, ohne sudo.")
    if args.action == "install":
        try:
            verify_package()
        except (OSError, ValueError, RuntimeError) as e:
            p.exit(1, f"Paketprüfung fehlgeschlagen: {e}\n")
    ctx = Context.current()
    if args.check:
        print("Paket-Prüfsummen: OK")
        print("Plasma:", run(["plasmashell", "--version"]) if shutil.which("plasmashell") else "nicht installiert (Ziel: Plasma 6.8.0)")
        print("Kvantum Qt6:", "vorhanden" if has_kvantum() else "fehlt; Breeze-Fallback verfügbar")
        print("Aurorae:", aurorae_plugin() or "nicht gefunden")
        print("App- und Plasma-Neustart: nach der Installation einmal ab- und anmelden")
        return
    try:
        with install_lock(ctx):
            if args.action == "install":
                install(ctx, args.install_only, not args.no_firefox)
            else:
                uninstall(ctx)
    except BlockingIOError:
        print("Ein anderer Liquid-Glass-Installer läuft bereits. Bitte diesen zuerst beenden.", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError) as e:
        print(f"Abgebrochen: {e}\nVorherige Daten sind gesichert. Rückgängig mit: bash uninstall.sh", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
