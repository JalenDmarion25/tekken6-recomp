from pathlib import Path
import json,datetime,shutil
root=Path(__file__).resolve().parents[1]
data=json.loads(Path(__file__).with_name('record_reset_toggle_patch.json').read_text())
support=root/'src/tekken6_record_menu_controls.inc'
if not support.is_file() or 'void RouteRecordPlaybackControlAction(' not in support.read_text():
 raise SystemExit('Missing menu support include. Extract the complete ZIP; no files changed.')
changes={}
for name,patches in data['patches'].items():
 path=root/name
 if not path.is_file():raise SystemExit(f'Missing {name}; no files changed.')
 text=path.read_text(encoding='utf-8');s=text
 for old,new in patches:
  if new in s:continue
  if s.count(old)!=1:raise SystemExit(f'Unexpected source layout in {name}; no files changed. Send this output.')
  s=s.replace(old,new,1)
 if s!=text:changes[path]=s
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path in changes:shutil.copy2(path,path.with_name(path.name+'.before-record-reset-toggle-'+stamp))
for path,text in changes.items():path.write_text(text,encoding='utf-8');print('Updated',path.relative_to(root))
print('Position Reset toggle and dark navy border installed. Rebuild and package next.' if changes else 'Position Reset toggle and dark navy border already installed and verified.')
