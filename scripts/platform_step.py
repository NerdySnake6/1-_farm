"""Run one native 1C operation against the isolated interface build database."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = Path('/Applications/1cv8t.localized/8.3.27.1688/1cv8t.app/Contents/MacOS/1cv8t')
DATABASE = (ROOT / sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / '.build/ui-base'


def main():
    """Dispatch an explicit development or export operation to Designer."""
    action = sys.argv[1]
    log = ROOT / '.build' / f'ui-{action}.log'
    restore_file = ROOT / 'deliverables/Farm_Lugovaya_v1.2.1.dt'
    if not restore_file.exists():
        restore_file = ROOT / 'deliverables/Farm_Lugovaya_v1.2.0.dt'
    if not restore_file.exists():
        restore_file = ROOT / 'deliverables/Farm_Lugovaya_v1.1.1.dt'
    if not restore_file.exists():
        restore_file = ROOT / 'deliverables/Farm_Lugovaya_v1.1.dt'
    if not restore_file.exists():
        restore_file = ROOT / 'deliverables/Farm_Lugovaya.dt'
    stages = {
        'restore': ['/RestoreIB', str(restore_file)],
        'load': ['/LoadConfigFromFiles', str(ROOT/'configuration')],
        'update': ['/UpdateDBCfg'],
        'check': ['/CheckConfig', '-Server', '-ThinClient', '-ThickClientManagedApplication'],
        'cf': ['/DumpCfg', str(ROOT/'deliverables/Farm_Lugovaya_v1.2.1.cf')],
        'dt': ['/DumpIB', str(ROOT/'deliverables/Farm_Lugovaya_v1.2.1.dt')],
        'source': ['/DumpConfigToFiles', str(ROOT/'.build/ui-source')],
    }
    if action == 'create':
        args = ['CREATEINFOBASE', f'File="{DATABASE}";Locale="ru_RU";']
    elif action == 'reservations':
        args = ['ENTERPRISE', '/F', str(DATABASE), '/N', 'Администратор', '/C', f'FarmReservationTests={ROOT}']
    elif action == 'tests':
        args = ['ENTERPRISE', '/F', str(DATABASE), '/N', 'Администратор', '/C', f'FarmTests={ROOT}']
    elif action in ['purchase', 'sales']:
        user = 'Покупка' if action == 'purchase' else 'Продажа'
        args = ['ENTERPRISE', '/F', str(DATABASE), '/N', user, '/C', f'FarmRole={ROOT}']
    elif action == 'show':
        args = ['ENTERPRISE', '/F', str(DATABASE), '/N', 'Администратор']
    else:
        args = ['DESIGNER', '/F', str(DATABASE)]
        if action != 'restore':
            args += ['/N', 'Администратор']
        args += stages[action]
    command = [str(APP), *args, '/Out', str(log), '/DisableStartupMessages', '/DisableStartupDialogs']
    result = subprocess.run(command, check=False)
    if log.exists():
        print(log.read_text(encoding='utf-8-sig'))
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
