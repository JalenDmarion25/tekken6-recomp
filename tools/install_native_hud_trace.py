from pathlib import Path
import shutil,datetime
root=Path(__file__).resolve().parents[1]
header=root/'src/tekken6_native_hud_trace.inc'
if not header.is_file():raise SystemExit('Extract the complete ZIP; diagnostic include missing.')
source=root/'src/tekken6_guest_hooks.cpp';config=root/'tekken6_config.toml'
text=source.read_text(encoding='utf-8-sig');cfg=config.read_text(encoding='utf-8-sig')
include='#include "tekken6_native_hud_trace.inc" // NATIVE PRACTICE HUD TRACE V1'
hook='''
# BEGIN NATIVE PRACTICE HUD TRACE V1
[[midasm_hook]]
address = 0x823612D4
name = "TraceNativePracticeHud"
registers = ["r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r12"]
# END NATIVE PRACTICE HUD TRACE V1

'''
changes={}
if include not in text:changes[source]=text+'\n'+include+'\n'
if '# BEGIN NATIVE PRACTICE HUD TRACE V1' not in cfg:
 if '0x823612d4' in cfg.lower() or cfg.count('[functions]')!=1:raise SystemExit('Unexpected hook configuration; no files changed.')
 changes[config]=cfg.replace('[functions]',hook+'[functions]',1)
elif hook.strip() not in cfg:raise SystemExit('Incomplete diagnostic configuration; no files changed.')
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-native-hud-trace-'+stamp))
for p,s in changes.items():p.write_text(s,encoding='utf-8');print('Updated',p.relative_to(root))
print('Native HUD diagnostic installed.' if changes else 'Native HUD diagnostic already installed and verified.')
