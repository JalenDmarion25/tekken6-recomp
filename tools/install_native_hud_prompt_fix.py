from pathlib import Path
import datetime
import re
import shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp'
config=root/'tekken6_config.toml'
header=root/'src/tekken6_native_hud_prompts.inc'
if not header.is_file():raise SystemExit('Extract the complete ZIP first. No files changed.')
text=source.read_text(encoding='utf-8-sig');cfg=config.read_text(encoding='utf-8-sig')
if '#include "tekken6_native_hud_layout.inc"' not in text:
    raise SystemExit('Install the previous combat HUD layout first. No files changed.')
pattern=r'(?ms)^\[\[midasm_hook\]\]\s*\n(?:(?!^\[).)*?address\s*=\s*0x8256[Bb]7[Ff]4\b(?:(?!^\[).)*'
matches=list(re.finditer(pattern,cfg))
if len(matches)!=1:raise SystemExit('Expected one full-scene diagnostic hook. No files changed.')
block=matches[0].group(0)
names=re.findall(r'^name\s*=\s*"([^"]+)"',block,re.M)
if names not in [['TraceNativePracticeHudScene'],['RepositionNativePracticeHudPrompts']]:
    raise SystemExit('Unexpected existing scene hook. No files changed.')
regs=re.findall(r'^registers\s*=\s*(\[[^\n]+\])',block,re.M)
if regs!=['["r31"]']:raise SystemExit('Unexpected scene hook registers. No files changed.')
block=re.sub(r'^name\s*=\s*"(?:TraceNativePracticeHudScene|RepositionNativePracticeHudPrompts)"',
             'name = "RepositionNativePracticeHudPrompts"',block,flags=re.M)
cfg=cfg[:matches[0].start()]+block+cfg[matches[0].end():]
include='#include "tekken6_native_hud_prompts.inc" // NATIVE PRACTICE PROMPT POSITIONS V1'
if include not in text:text+='\n'+include+'\n'
changes={p:v for p,v in ((source,text),(config,cfg)) if p.read_text(encoding='utf-8-sig')!=v}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-hud-prompt-positions-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Native prompt position fix installed. Rebuild and package next.' if changes else 'Native prompt position fix already installed and verified.')
