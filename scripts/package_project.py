"""Package only current documentation, source evidence and 1C exports."""
import hashlib
import json
from zipfile import ZIP_DEFLATED, ZipFile

from check_documentation import check
from document_common import FACTS, ROOT

VERSION = FACTS['configuration_version']
OUTPUT = ROOT / f'deliverables/Комплект_Молочная_ферма_v{VERSION}.zip'
PREFIX = 'Молочная_ферма/'


def current_files():
    """Select portable sources and current exports, excluding all old versions."""
    files = [ROOT / 'README.md']
    files.extend(ROOT / f'deliverables/Farm_Lugovaya_v{VERSION}.{suffix}' for suffix in ['dt', 'cf'])
    for name in ['Документация', 'assets', 'configuration', 'scripts']:
        for path in sorted((ROOT / name).rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            if any(part in {'Архив', '__pycache__', 'node_modules', '.build'} for part in path.parts):
                continue
            if path.name == '.DS_Store' or path.suffix in {'.pyc', '.zip', '.pdf'}:
                continue
            files.append(path)
    assert len(files) == len(set(files))
    assert all(path.exists() for path in files)
    return sorted(files)


def package():
    """Validate and build a ZIP, then verify every packaged file against SHA-256."""
    OUTPUT.parent.mkdir(exist_ok=True)
    check(pending_package=True)
    paths = current_files()
    manifest = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    staged = OUTPUT.with_suffix('.zip.tmp')
    with ZipFile(staged, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(path, PREFIX + path.relative_to(ROOT).as_posix())
        archive.writestr(PREFIX + 'SHA256.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    with ZipFile(staged) as archive:
        assert archive.testzip() is None
        for name, checksum in manifest.items():
            assert hashlib.sha256(archive.read(PREFIX + name)).hexdigest() == checksum, name
        assert len(archive.namelist()) == len(manifest) + 1
        assert not any('/Архив/' in name or '/.build/' in name for name in archive.namelist())
    staged.replace(OUTPUT)
    print(f'{OUTPUT}: {len(paths)} files, {OUTPUT.stat().st_size} bytes')


if __name__ == '__main__':
    package()
