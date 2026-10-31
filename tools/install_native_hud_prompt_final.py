from pathlib import Path
import datetime
import re
import shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp';config=root/'tekken6_config.toml'
header=root/'src/tekken6_native_hud_prompt_render.inc'
if not header.is_file() or 'native-practice-hud-final-transform.txt' not in header.read_text(encoding='utf-8-sig'):
    raise SystemExit('Extract the complete final-transform ZIP first. No files changed.')
text=source.read_text(encoding='utf-8-sig');cfg=config.read_text(encoding='utf-8-sig')
if '#include "tekken6_native_hud_prompt_render.inc"' not in text:raise SystemExit('Previous prompt render fix not installed. No files changed.')
pattern=r'(?ms)^\[\[midasm_hook\]\][ \t]*\r?\n(?:(?!^\[|^#).)*?address\s*=\s*0x8256(?:[Dd][Bb]40|[Dd][Ee]18)\b(?:(?!^\[|^#).)*'
matches=list(re.finditer(pattern,cfg))
if len(matches)!=1:raise SystemExit('Expected one prompt transform hook. No files changed.')
block=matches[0].group(0)
if not re.search(r'^name\s*=\s*"RepositionNativePracticeHudPromptBeforeDraw"',block,re.M):raise SystemExit('Unexpected transform hook. No files changed.')
if re.findall(r'^registers\s*=\s*(\[[^\n]+\])',block,re.M)!=['["r31"]']:raise SystemExit('Unexpected hook registers. No files changed.')
block=re.sub(r'0x8256(?:[Dd][Bb]40|[Dd][Ee]18)\b','0x8256DE18',block,count=1)
updated=cfg[:matches[0].start()]+block+cfg[matches[0].end():]
if updated!=cfg:
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    shutil.copy2(config,config.with_name(config.name+'.before-final-prompt-transform-'+stamp))
    config.write_text(updated,encoding='utf-8')
    print('Moved prompt adjustment after final native transforms. Rebuild and package next.')
else:print('Final prompt transform hook already installed and verified.')
