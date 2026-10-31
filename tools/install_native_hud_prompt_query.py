from pathlib import Path
import datetime,re,shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp';config=root/'tekken6_config.toml'
if not (root/'src/tekken6_native_hud_prompt_query.inc').is_file() or not (root/'src/tekken6_native_hud_prompts.inc').is_file():
    raise SystemExit('Extract the complete ZIP after the previous prompt patches. No files changed.')
text=source.read_text(encoding='utf-8-sig');cfg=config.read_text(encoding='utf-8-sig')
if '#include "tekken6_native_hud_prompts.inc"' not in text:raise SystemExit('Prompt helpers missing. No files changed.')
pattern=r'(?ms)^\[\[midasm_hook\]\][ \t]*\r?\n(?:(?!^\[|^#).)*?address\s*=\s*0x8256(?:[Dd][Bb]40|[Dd][Ee]18)\b(?:(?!^\[|^#).)*'
matches=list(re.finditer(pattern,cfg))
if len(matches)>1:raise SystemExit('Multiple transform hooks found. No files changed.')
if matches:
    block=matches[0].group(0)
    if not re.search(r'^name\s*=\s*"RepositionNativePracticeHudPromptBeforeDraw"',block,re.M):raise SystemExit('Unexpected transform hook. No files changed.')
    cfg=cfg[:matches[0].start()]+cfg[matches[0].end():]
hooks='''# BEGIN NATIVE PRACTICE PROMPT QUERY V1
[[midasm_hook]]
address = 0x8256C8CC
name = "AdjustNativePracticePromptCoordinates"
registers = ["r3", "r4", "r5"]
# END NATIVE PRACTICE PROMPT QUERY V1

'''
if '# BEGIN NATIVE PRACTICE PROMPT QUERY V1' not in cfg:
    if not matches or '0x8256c8cc' in cfg.lower() or cfg.count('[functions]')!=1:raise SystemExit('Unexpected query-hook configuration. No files changed.')
    cfg=cfg.replace('[functions]',hooks+'[functions]',1)
elif hooks.strip() not in cfg:raise SystemExit('Incomplete query hook. No files changed.')
include='#include "tekken6_native_hud_prompt_query.inc" // NATIVE PRACTICE PROMPT QUERY V1'
if include not in text:text+='\n'+include+'\n'
changes={p:v for p,v in ((source,text),(config,cfg)) if p.read_text(encoding='utf-8-sig')!=v}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-prompt-query-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Coordinate-query correction installed. Rebuild and package next.' if changes else 'Coordinate-query correction already installed and verified.')
