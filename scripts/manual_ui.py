"""Record authorized AppleScript interaction with the isolated 1C test window."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'Документация/04_Тестирование/Протоколы/Ручные/RUN-20261024-01'
PID = 57312


def run_action(action, label):
    """Execute a visible UI action and record its exact AppleScript text."""
    script = f'tell application "System Events" to set isFront to frontmost of (first application process whose unix id is {PID})\nif not isFront then tell application "/Applications/1cv8t.localized/8.3.27.1688/1cv8ct.app" to activate\ntell application "System Events"\n tell (first application process whose unix id is {PID})\ndelay 1\n{action}\ndelay 1\n end tell\nend tell'
    result = subprocess.run(['osascript', '-e', script], text=True, capture_output=True, check=False)
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / 'ui-actions.jsonl').open('a') as stream:
        stream.write(json.dumps({'time': datetime.now().astimezone().isoformat(), 'label': label, 'script': script, 'returncode': result.returncode, 'output': result.stdout, 'error': result.stderr}, ensure_ascii=False) + '\n')
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def capture(name):
    """Capture the unmodified application rectangle into the evidence folder."""
    target = RUN / (name + '.png')
    geometry = run_action('return {position of (first window whose name is \"Молочная ферма\"), size of (first window whose name is \"Молочная ферма\")}', name + '-capture')
    rectangle = ','.join(part.strip() for part in geometry.split(','))
    subprocess.run(['screencapture', '-x', '-R' + rectangle, str(target)], check=True)
    print(target)


def main():
    """Run an optional action and capture its visible outcome."""
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--script', default='')
    parser.add_argument('--click', nargs=2, type=int)
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--click-sequence', type=json.loads)
    args = parser.parse_args()
    clicks = args.click_sequence or ([args.click] if args.click else [])
    if clicks:
        run_action('', args.name + '-activate')
        points = json.dumps(clicks)
        mouse_script = f'''ObjC.import('ApplicationServices');
for(var xy of {points}){{
var point=$.CGPointMake(xy[0],xy[1]);
$.CGWarpMouseCursorPosition(point);
$.CGEventPost(0,$.CGEventCreateMouseEvent(null,5,point,0));
delay(0.2);
for(var i=1;i<={args.count};i++){{
 var down=$.CGEventCreateMouseEvent(null,1,point,0);
 var up=$.CGEventCreateMouseEvent(null,2,point,0);
 $.CGEventSetIntegerValueField(down,1,i);
 $.CGEventSetIntegerValueField(up,1,i);
 $.CGEventPost(0,down);delay(0.07);$.CGEventPost(0,up);delay(0.1);
}}
delay(0.8);
}}'''
        subprocess.run(['osascript', '-l', 'JavaScript', '-e', mouse_script], check=True)
        with (RUN / 'ui-actions.jsonl').open('a') as stream:
            stream.write(json.dumps({'time':datetime.now().astimezone().isoformat(),'label':args.name,'mouse_sequence':clicks,'click_count':args.count},ensure_ascii=False)+'\n')
    if args.script:
        print(run_action(args.script, args.name))
    else:
        RUN.mkdir(parents=True, exist_ok=True)
    capture(args.name)


if __name__ == '__main__':
    main()
