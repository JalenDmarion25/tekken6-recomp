from pathlib import Path
import datetime
import re
import shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp';config=root/'tekken6_config.toml'
if not (root/'src/tekken6_native_hud_prompt_render.inc').is_file() or not (root/'src/tekken6_native_hud_prompts.inc').is_file():
    raise SystemExit('Extract the complete ZIP after installing the previous prompt fix. No files changed.')
text=source.read_text(encoding='utf-8-sig');cfg=config.read_text(encoding='utf-8-sig')
if '#include "tekken6_native_hud_prompts.inc"' not in text:raise SystemExit('Previous prompt fix not installed. No files changed.')
# Remove the late hook, leaving its helper include available to the new hook.
pattern=r'(?ms)^\[\[midasm_hook\]\][ \t]*\r?\n(?:(?!^\[|^#).)*?address\s*=\s*0x8256[Bb]7[Ff]4\b(?:(?!^\[|^#).)*'
matches=list(re.finditer(pattern,cfg))
if len(matches)>1:raise SystemExit('Duplicate late scene hooks. No files changed.')
if matches:
    block=matches[0].group(0)
    if not re.search(r'^name\s*=\s*"RepositionNativePracticeHudPrompts"',block,re.M):raise SystemExit('Unexpected late scene hook. No files changed.')
    cfg=cfg[:matches[0].start()]+cfg[matches[0].end():]
hooks='''# BEGIN NATIVE HUD PROMPT DRAW V2
[[midasm_hook]]
address = 0x8256DB40
name = "RepositionNativePracticeHudPromptBeforeDraw"
registers = ["r31"]
# END NATIVE HUD PROMPT DRAW V2

'''
if '# BEGIN NATIVE HUD PROMPT DRAW V2' not in cfg:
    if '0x8256db40' in cfg.lower() or cfg.count('[functions]')!=1:raise SystemExit('Conflicting drawing hook. No files changed.')
    if not matches:raise SystemExit('Expected the previously installed prompt hook. No files changed.')
    cfg=cfg.replace('[functions]',hooks+'[functions]',1)
elif hooks.strip() not in cfg:raise SystemExit('Incomplete drawing hook. No files changed.')
include='#include "tekken6_native_hud_prompt_render.inc" // NATIVE HUD PROMPT DRAW V2'
if include not in text:text+='\n'+include+'\n'
changes={p:v for p,v in ((source,text),(config,cfg)) if p.read_text(encoding='utf-8-sig')!=v}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-prompt-draw-fix-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Prompt fix moved before native drawing. Rebuild and package next.' if changes else 'Prompt drawing fix already installed and verified.')
