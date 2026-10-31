from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_guest_hooks.cpp'
support=root/'src/tekken6_record_opponent_clear.inc'
if not support.is_file() or 'void ObserveRecordedOpponent(' not in support.read_text():
 raise SystemExit('Missing opponent-change support file. Extract the complete ZIP; no source files changed.')
text=path.read_text(encoding='utf-8-sig');s=text
signature='void NativeDummyControlTest(PPCRegister &selected, PPCRegister &owner) {'
include='#include "tekken6_record_opponent_clear.inc" // RECORD OPPONENT CLEAR V1'
if include not in s:
 if s.count(signature)!=1:raise SystemExit('Unexpected native dummy hook layout; no source files changed.')
 s=s.replace(signature,include+'\n'+signature,1)
start=s.index(signature)
end=s.find('// END NATIVE DUMMY CONTROL TEST V1',start)
if end<0:raise SystemExit('Native dummy hook boundary not found; no source files changed.')
body=s[start:end]
call='  ObserveRecordedOpponent(b,c); // RECORD OPPONENT CLEAR V1'
anchor='  if (!c || owner.u32!=c || read(b,c)!=0x8207D3E4u || active()) return;'
if call not in body:
 if body.count(anchor)!=1:raise SystemExit('Unexpected practice-owner guard; no source files changed.')
 body=body.replace(anchor,anchor+'\n'+call,1)
 s=s[:start]+body+s[end:]
if s==text:print('Opponent-change recording clear already installed and verified.')
else:
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 shutil.copy2(path,path.with_name(path.name+'.before-record-opponent-clear-'+stamp))
 path.write_text(s,encoding='utf-8');print('Installed clearing recordings when the opponent character changes. Rebuild and package next.')
