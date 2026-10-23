#!/usr/bin/env python3
"""Build the standalone ZIP, integrity manifest and SHA-256 sidecar."""
from pathlib import Path
import hashlib
import json
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'package'


def main():
    version = json.loads((PACKAGE / 'design/vitalux.json').read_text())['version']
    name = 'Vitalux-Liquid-Silver-openSUSE-' + version
    files = sorted(path for path in PACKAGE.rglob('*')
                   if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
                   and path.name != 'SHA256SUMS.json')
    if any(path.is_symlink() for path in files):
        raise ValueError('Release payload must not contain symlinks')
    manifest = {str(path.relative_to(PACKAGE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    manifest_file = PACKAGE / 'SHA256SUMS.json'
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    output = ROOT / 'downloads'
    output.mkdir(exist_ok=True)
    archive = output / (name + '.zip')
    temporary = archive.with_suffix('.zip.part')
    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for path in sorted([*files, manifest_file]):
            info = zipfile.ZipInfo(name + '/' + str(path.relative_to(PACKAGE)))
            info.create_system = 3
            launcher = path.parent == PACKAGE and path.suffix == '.desktop'
            mode = 0o755 if launcher or path.name in ('install.sh', 'uninstall.sh', 'run-installer.sh') else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            target.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    temporary.replace(archive)
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + '.sha256').write_text(checksum + '  ' + archive.name + '\n')
    print(f'{archive.name}: {archive.stat().st_size} bytes, {len(files) + 1} files')
    print('SHA-256: ' + checksum)


if __name__ == '__main__':
    main()
