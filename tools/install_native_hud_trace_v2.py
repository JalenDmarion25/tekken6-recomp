from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp';config=root/'tekken6_config.toml';trace=root/'src/tekken6_native_hud_trace.inc'
if not trace.is_file() or not (root/'src/tekken6_native_hud_objects_trace.inc').is_file():raise SystemExit('Extract the complete ZIP; required diagnostic include missing.')
changes={}
text=source.read_text(encoding='utf-8-sig');include='#include "tekken6_native_hud_objects_trace.inc" // NATIVE HUD OBJECT TRACE V2'
if include not in text:changes[source]=text+'\n'+include+'\n'
cfg=config.read_text(encoding='utf-8-sig')
hooks='''
# BEGIN NATIVE HUD OBJECT TRACE V2
[[midasm_hook]]
address = 0x82367214
name = "TraceNativePracticeHudObject"
registers = ["r3", "r12"]

[[midasm_hook]]
address = 0x82463574
name = "TraceNativePracticeHudAnimations"
registers = ["r3", "r12"]
# END NATIVE HUD OBJECT TRACE V2

'''
if '# BEGIN NATIVE HUD OBJECT TRACE V2' not in cfg:
 if cfg.count('[functions]')!=1 or any(a in cfg.lower() for a in ['0x82367214','0x82463574']):raise SystemExit('Unexpected hook configuration; no files changed.')
 changes[config]=cfg.replace('[functions]',hooks+'[functions]',1)
elif hooks.strip() not in cfg:raise SystemExit('Incomplete HUD object hooks; no files changed.')
s=trace.read_text(encoding='utf-8-sig')
old=' const uint64_t key=uint64_t(caller.u32)<<32|format.u32;'
new=''' uint64_t key=uint64_t(caller.u32)<<32|format.u32;
 // NATIVE HUD OBJECT TRACE V2: distinguish combo, total damage and counter labels.
 if(caller.u32==0x824623ECu || caller.u32==0x8246247Cu || caller.u32==0x82462634u)
   key^=uint64_t(f.u32)<<1;'''
if new not in s:
 if s.count(old)!=1:raise SystemExit('Unexpected original HUD trace layout; no files changed.')
 changes[trace]=s.replace(old,new,1)
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-hud-objects-'+stamp))
for p,t in changes.items():p.write_text(t,encoding='utf-8');print('Updated',p.relative_to(root))
print('HUD object diagnostic installed.' if changes else 'HUD object diagnostic already installed and verified.')
