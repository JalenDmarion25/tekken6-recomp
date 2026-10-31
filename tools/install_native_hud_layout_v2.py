from pathlib import Path
import datetime
import re
import shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp'
config=root/'tekken6_config.toml'
header=root/'src/tekken6_native_hud_layout.inc'
if not header.is_file() or not (root/'src/tekken6_native_hud_scene_trace.inc').is_file():raise SystemExit('Extract the complete ZIP first. No files changed.')
text=source.read_text(encoding='utf-8-sig')
cfg=config.read_text(encoding='utf-8-sig')
include='#include "tekken6_native_hud_layout.inc" // NATIVE HUD LAYOUT V1'
if include not in text:text+='\n'+include+'\n'
scene_include='#include "tekken6_native_hud_scene_trace.inc" // NATIVE HUD SCENE TRACE V1'
if scene_include not in text:text+='\n'+scene_include+'\n'
# Reuse the existing formatted-text hook, never register two at one address.
pattern=r'(?ms)^\[\[midasm_hook\]\]\s*\n(?:(?!^\[).)*?address\s*=\s*0x823612[Dd]4\b(?:(?!^\[).)*'
matches=list(re.finditer(pattern,cfg))
if len(matches)!=1:raise SystemExit('Expected exactly one installed HUD text diagnostic hook. No files changed.')
block=matches[0].group(0)
names=re.findall(r'^name\s*=\s*"([^"]+)"',block,re.M)
if names not in [['TraceNativePracticeHud'],['AdjustNativePracticeHud']]:
    raise SystemExit('Unexpected existing text hook. No files changed.')
block=block.replace('name = "TraceNativePracticeHud"','name = "AdjustNativePracticeHud"')
if 'name = "AdjustNativePracticeHud"' not in block:raise SystemExit('Unexpected hook formatting. No files changed.')
cfg=cfg[:matches[0].start()]+block+cfg[matches[0].end():]
hooks='''# BEGIN NATIVE HUD NODE TRACE V1
[[midasm_hook]]
address = 0x8254AF5C
name = "BeginNativePracticeHudNode"
registers = ["r3", "r4", "r12"]

[[midasm_hook]]
address = 0x8254AF68
name = "InspectNativePracticeHudNode"
registers = ["r3"]
# END NATIVE HUD NODE TRACE V1

'''
if '# BEGIN NATIVE HUD NODE TRACE V1' not in cfg:
    if any(address.lower() in cfg.lower() for address in ('0x8254AF5C','0x8254AF68')) or cfg.count('[functions]')!=1:
        raise SystemExit('Conflicting node hooks. No files changed.')
    cfg=cfg.replace('[functions]',hooks+'[functions]',1)
elif hooks.strip() not in cfg:raise SystemExit('Incomplete node hooks. No files changed.')
scene_hooks='# BEGIN NATIVE HUD SCENE TRACE V1\n[[midasm_hook]]\naddress = 0x8256B7F4\nname = "TraceNativePracticeHudScene"\nregisters = ["r31"]\n# END NATIVE HUD SCENE TRACE V1\n\n'
if '# BEGIN NATIVE HUD SCENE TRACE V1' not in cfg:
    if '0x8256b7f4' in cfg.lower() or cfg.count('[functions]')!=1:raise SystemExit('Conflicting scene hook. No files changed.')
    cfg=cfg.replace('[functions]',scene_hooks+'[functions]',1)
elif scene_hooks.strip() not in cfg:raise SystemExit('Incomplete scene hook. No files changed.')
changes={p:v for p,v in ((source,text),(config,cfg)) if p.read_text(encoding='utf-8-sig')!=v}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-native-hud-layout-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Combat HUD and WALL HIT positions installed; bottom prompts unchanged.' if changes else 'HUD layout already installed and verified.')
