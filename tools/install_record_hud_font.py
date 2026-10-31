from pathlib import Path
import datetime,json,shutil,hashlib
root=Path(__file__).resolve().parents[1]
data=json.loads(Path(__file__).with_name('record_hud_font_patch.json').read_text())
inc=root/'src/tekken6_record_hud_font.inc'
if not inc.is_file() or hashlib.sha256(inc.read_bytes()).hexdigest()!=data['header_sha256']:
 raise SystemExit('Missing or incomplete font support file. Extract the entire ZIP into the project; no source files changed.')
path=root/'src/tekken6_app.h';text=path.read_text(encoding='utf-8');s=text
for old,new in data['patches']:
 if new in s:continue
 if s.count(old)!=1:raise SystemExit('Unexpected HUD source layout; no source files changed. Send this output.')
 s=s.replace(old,new,1)
if s==text:print('Racing Sans One HUD font already installed and verified.')
else:
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 shutil.copy2(path,path.with_name(path.name+'.before-record-hud-font-'+stamp))
 path.write_text(s,encoding='utf-8');print('Installed Racing Sans One for the recording HUD. Rebuild and package next.')
