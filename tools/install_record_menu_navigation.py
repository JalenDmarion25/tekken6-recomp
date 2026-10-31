from pathlib import Path
import datetime,json,shutil
root=Path(__file__).resolve().parents[1]
data=json.loads(Path(__file__).with_name('record_menu_navigation_patch.json').read_text())
changes={}
for name,addition in data['append'].items():
 path=root/name
 if not path.is_file():raise SystemExit(f'Missing {name}; no files changed.')
 text=path.read_text(encoding='utf-8')
 marker='void ObserveRecordingStartRelease(' if name.endswith('flow.inc') else 'void GuardRecordPlaybackRootBack('
 if marker in text:
  if addition.strip() not in text:raise SystemExit(f'Unexpected existing navigation fix in {name}; no files changed.')
  continue
 if name.endswith('flow.inc') and 'void FilterRecordingStart(' not in text:raise SystemExit('Recording flow support is missing; no files changed.')
 if name.endswith('apply.inc') and 'void FinishRecordMenuCloseQuery(' not in text:raise SystemExit('Slot menu close support is missing; no files changed.')
 changes[path]=text+'\n'+addition
path=root/'tekken6_config.toml';text=path.read_text(encoding='utf-8')
if '# BEGIN RECORD MENU NAVIGATION V1' not in text:
 for address in ('0x82268108','0x824365E0'):
  if address.lower() in text.lower():raise SystemExit(f'Hook address {address} already in use; no files changed.')
 if text.count('[functions]')!=1:raise SystemExit('Unexpected hook configuration; no files changed.')
 changes[path]=text.replace('[functions]',data['config']+'[functions]',1)
elif data['config'].strip() not in text:raise SystemExit('Incomplete navigation hooks; no files changed.')
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for path in changes:shutil.copy2(path,path.with_name(path.name+'.before-record-navigation-'+stamp))
for path,text in changes.items():path.write_text(text,encoding='utf-8');print('Updated',path.relative_to(root))
print('Record menu navigation fix installed. Rebuild and package next.' if changes else 'Record menu navigation fix already installed and verified.')
