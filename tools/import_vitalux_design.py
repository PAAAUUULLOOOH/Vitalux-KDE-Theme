#!/usr/bin/env python3
"""Extract a named Vitalux design without executing the source application.

The original source/notice and hashes travel with the derived artwork. Run with
the development PySide6 runtime to render its exact QPainter wallpaper.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'package'


def extract_palette(source: Path, skin: str):
    if skin == 'liquid_silver':
        tree = ast.parse((source / 'vitalux/premium.py').read_text())
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if (isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
                    and target.value.id == 'COLLECTIONS'
                    and isinstance(target.slice, ast.Constant) and target.slice.value == skin):
                value = node.value
                if not isinstance(value, ast.Call) or not isinstance(value.func, ast.Name) or value.func.id != 'dict' or value.args:
                    raise ValueError('Unsupported Vitalux palette expression')
                return {item.arg: ast.literal_eval(item.value) for item in value.keywords}
    elif skin == 'glass':
        tree = ast.parse((source / 'vitalux/theme.py').read_text())
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_THEMES' for t in node.targets):
                result = ast.literal_eval(node.value)[skin]
                # The base Glass design has a user/distro-selected accent.
                # Require that value explicitly instead of inventing a color.
                return dict(result, title='Glass', subtitle='VITALUX GLASS')
    raise ValueError(f'Design not found in the supplied Vitalux source: {skin}')


def record_source(source: Path, skin: str, accent: str | None = None):
    palette = extract_palette(source, skin)
    if skin == 'glass':
        if accent is None:
            raise ValueError('Glass uses a selected accent; pass its original --accent value.')
        palette.update(accent=accent, secondary=palette['text'], light=palette['border'],
                       bloom=palette['sidebar'], shadow=palette['bg'])
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    folder = PACKAGE / 'reference/vitalux'
    folder.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in ('vitalux/premium.py', 'vitalux/theme.py', 'vitalux/signature_designs.py', 'LICENSE-NOTICE.md'):
        path = source / name
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        shutil.copyfile(path, folder / path.name)
    document = {
        'version': '1.1.0',
        'name': 'Vitalux Liquid Silver' if skin == 'liquid_silver' else 'Vitalux Glass',
        'source': {
            'repository': 'https://github.com/PAAAUUULLOOOH/Vitalux',
            'commit': commit,
            'skin': skin,
            'display_name': palette['title'],
            'files': hashes,
        },
        'colors': palette,
        # Same blend() formula/strengths as Vitalux theme.stylesheet().
        'controls': {
            name: '#' + ''.join(f'{round(int(palette["accent"][i:i+2], 16) * strength + int(palette[base][i:i+2], 16) * (1-strength)):02x}' for i in (1, 3, 5))
            for name, base, strength in (
                ('input_bg', 'card', .045), ('button_bg', 'card', .10),
                ('active_bg', 'sidebar', .22), ('hover_border', 'border', .60),
            )
        },
        'material': {
            'radius': {'panel': 21, 'strong': 25, 'compact': 12},
            'wash': [[0, 'card', 167], [0.45, 'bg', 202], [1, 'card', 210]],
            'strong_wash': [[0, 'card', 185], [0.45, 'bg', 215], [1, 'card', 210]],
            'edge': [[0, 'secondary', 125], [0.18, 'accent', 90], [0.4, 'border', 49],
                     [0.62, 'accent', 62], [0.83, 'border', 38], [1, 'secondary', 82]],
            'inner_edge': {'color': '#ffffff', 'alpha': 20, 'inset': 2},
            'sheen': [[0, '#ffffff', 21], [0.13, '#ffffff', 3], [0.6, '#ffffff', 0], [1, '#000000', 23]],
        },
    }
    path = PACKAGE / 'design/vitalux.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + '\n')
    return document


def render_wallpaper(source: Path, document):
    from PySide6.QtCore import QPointF, QRectF, QSize, Qt
    from PySide6.QtGui import QBrush, QColor, QGuiApplication, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient

    app = QGuiApplication.instance() or QGuiApplication([])
    skin = document['source']['skin']
    if skin == 'liquid_silver':
        import types
        original = (source / 'vitalux/premium.py').read_text()
        tree = ast.parse(original)
        functions = [ast.get_source_segment(original, n) for n in tree.body
                     if isinstance(n, ast.FunctionDef) and n.name in ('palette', 'color', 'scene_pixmap')]
        context = dict(locals(), COLLECTIONS={skin: document['colors']},
                       signature_designs=types.SimpleNamespace(KEYS=()))
        # These are the pinned Vitalux drawing functions, not the full app.
        exec(compile('\n\n'.join(functions), 'Vitalux original wallpaper renderer', 'exec'), context)
        pixmap = context['scene_pixmap'](QSize(3840, 2160), skin)
    else:
        pixmap = QPixmap(str(source / 'assets/glass-atmosphere.jpg'))
        if pixmap.isNull():
            raise ValueError('Original Glass wallpaper is missing')
    images = PACKAGE / 'payload/wallpapers/LiquidGlass/contents/images'
    images.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(images / '3840x2160.jpg'), 'JPG', 98):
        raise RuntimeError('Original wallpaper could not be exported')
    (images / '3840x2160.svg').unlink(missing_ok=True)
    if not pixmap.save(str(PACKAGE / 'reference/vitalux/wallpaper-original.png'), 'PNG'):
        raise RuntimeError('Lossless reference wallpaper could not be exported')
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--skin', required=True, choices=('liquid_silver', 'glass'))
    parser.add_argument('--accent')
    args = parser.parse_args()
    document = record_source(args.source, args.skin, args.accent)
    render_wallpaper(args.source, document)
    print('Imported exact Vitalux reference:', document['source']['display_name'], document['source']['commit'])


if __name__ == '__main__':
    main()
