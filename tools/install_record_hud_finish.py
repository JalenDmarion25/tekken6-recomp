from pathlib import Path
import json,datetime,shutil
root=Path(__file__).resolve().parents[1]
data=json.loads(Path(__file__).with_name('record_hud_finish_patch.json').read_text())
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
inc=root/'src/tekken6_record_hud_finish.inc'
if not inc.is_file() or 'void RecordFinishPauseInput(' not in inc.read_text():
 raise SystemExit('Missing HUD support file. Extract the complete archive into the project; no files changed.')
path=root/'tekken6_config.toml';text=path.read_text();s=text
if '# BEGIN RECORD HUD FINISH V1' not in s:
 if s.count('[functions]')!=1:raise SystemExit('Unexpected hook configuration; no files changed.')
 for address in ('0x8238EFBC','0x824631B8'):
  if address.lower() in s.lower():raise SystemExit('Hook address already in use; no files changed. Send this output.')
 s=s.replace('[functions]',data['config']+'[functions]',1)
elif data['config'].strip() not in s:
 raise SystemExit('Incomplete HUD hook configuration; no files changed. Send this output.')
if s!=text:changes[path]=s
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path in changes:shutil.copy2(path,path.with_name(path.name+'.before-record-hud-finish-'+stamp))
for path,s in changes.items():path.write_text(s,encoding='utf-8');print('Updated',path.relative_to(root))
print('Recording HUD and finish update installed. Rebuild and package next.' if changes else 'Recording HUD and finish update already installed and verified.')
