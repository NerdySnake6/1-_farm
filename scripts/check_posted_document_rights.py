"""Check posted-document form permissions in a newly restored, isolated 1C base."""

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_V8 = Path('/Applications/1cv8t.localized/8.3.27.1688/1cv8t.app/Contents/MacOS/1cv8t')


def run_native(executable, work, name, arguments):
    """Run a bounded platform command and preserve the native log."""
    log = work / (name + '.txt')
    result = subprocess.run(
        [str(executable), *arguments, '/Out', str(log),
         '/DisableStartupMessages', '/DisableStartupDialogs'],
        capture_output=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        details = log.read_text(encoding='utf-8-sig') if log.exists() else ''
        raise RuntimeError(f'{name}: exit {result.returncode}\n{details}')
    print(f'OK: {name}', flush=True)


def main():
    """Prepare test-only hooks and verify each role without editing working bases."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v8-path', type=Path, default=DEFAULT_V8)
    parser.add_argument('--dt', type=Path, default=ROOT / 'deliverables/Farm_Lugovaya_v1.2.1.dt')
    parser.add_argument('--source', type=Path, default=ROOT / 'configuration')
    parser.add_argument('--work-dir', type=Path)
    args = parser.parse_args()
    work = (args.work_dir or ROOT / '.build' / datetime.now().strftime('posted-rights-%Y%m%d-%H%M%S')).resolve()
    if not args.v8_path.is_file() or not args.dt.is_file():
        parser.error('Platform executable and input DT must exist.')
    work.mkdir(parents=True, exist_ok=False)
    source = work / 'source'
    shutil.copytree(args.source, source)
    app = source / 'Ext/ManagedApplicationModule.bsl'
    marker = 'Процедура ПриНачалеРаботыСистемы()'
    text = app.read_text(encoding='utf-8-sig')
    if text.count(marker) != 1:
        raise RuntimeError('Expected one application startup handler.')
    client = (ROOT / 'scripts/bsl/ПраваПроведенныхКлиент.bsl').read_text(encoding='utf-8-sig')
    app.write_text(text.replace(marker, marker + '\n' + client, 1), encoding='utf-8-sig')
    service = source / 'CommonModules/СервисФермы/Ext/Module.bsl'
    server = (ROOT / 'scripts/bsl/ПраваПроведенныхСервер.bsl').read_text(encoding='utf-8-sig')
    service.write_text(service.read_text(encoding='utf-8-sig') + '\n' + server, encoding='utf-8-sig')
    base = work / 'base'
    run_native(args.v8_path, work, 'create', ['CREATEINFOBASE', f'File="{base}";Locale="ru_RU";'])
    run_native(args.v8_path, work, 'restore', ['DESIGNER', '/F', str(base), '/RestoreIB', str(args.dt.resolve())])
    connection = ['DESIGNER', '/F', str(base), '/N', 'Администратор']
    run_native(args.v8_path, work, 'load', [*connection, '/LoadConfigFromFiles', str(source)])
    run_native(args.v8_path, work, 'update', [*connection, '/UpdateDBCfg'])
    run_native(args.v8_path, work, 'check', [*connection, '/CheckConfig', '-Server', '-ThinClient', '-ThickClientManagedApplication'])
    for user, count in [('Покупка', 9), ('Продажа', 20), ('Администратор', 26)]:
        run_native(args.v8_path, work, user, [
            'ENTERPRISE', '/F', str(base), '/N', user, '/C', 'FarmPostedTests=' + str(work),
        ])
        result = (work / ('posted-' + user + '.txt')).read_text(encoding='utf-8-sig')
        actual = sum(line.startswith('PASS |') for line in result.splitlines())
        if 'ERROR |' in result or 'COMPLETE' not in result or actual != count:
            raise RuntimeError(f'{user}: expected {count} successful checks\n{result}')
    print(f'PASS: 55 form and permission checks. Results: {work}')


if __name__ == '__main__':
    main()
