from pathlib import Path
import json,datetime,shutil
root=Path(__file__).resolve().parents[1]
data=json.loads(Path(__file__).with_name('record_flow_patch.json').read_text())
changes={}
for name,patches in data['patches'].items():
 path=root/name;text=path.read_text(encoding='utf-8');s=text
 for old,new in patches:
  if new in s:continue
  if s.count(old)!=1:raise SystemExit(f'Unexpected source layout in {name}; no files changed. Send this output.')
  s=s.replace(old,new,1)
 if name.endswith('tekken6_quick_select_apply.inc'):
  if 'void FinishRecordMenuCloseQuery(' not in s:s+='\n'+data['close']
 if s!=text:changes[path]=s
path=root/'tekken6_config.toml';text=path.read_text();s=text
if '# BEGIN RECORD FLOW V1' not in s:
 if s.count('[functions]')!=1:raise SystemExit('Unexpected hook configuration; no files changed.')
 s=s.replace('[functions]',data['config']+'[functions]',1)
if s!=text:changes[path]=s
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path in changes:shutil.copy2(path,path.with_name(path.name+'.before-record-flow-'+stamp))
for path,s in changes.items():path.write_text(s,encoding='utf-8');print('Updated',path.relative_to(root))
print('Record flow changes installed.' if changes else 'Record flow changes already installed and verified.')
