from pathlib import Path
import datetime,re,shutil
root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp'
config=root/'tekken6_config.toml'
text=source.read_text(encoding='utf-8-sig')
cfg=config.read_text(encoding='utf-8-sig')
if not (root/'src/tekken6_practice_prompt_widget.inc').is_file():
    raise SystemExit('Extract the complete ZIP first. No changes made.')
start='# BEGIN PRACTICE WIDGET DRAW TRACE V1'
end='# END PRACTICE WIDGET DRAW TRACE V1'
if start in cfg:
    if cfg.count(start)!=1 or cfg.count(end)!=1:raise SystemExit('Unexpected diagnostic block; no changes made.')
    cfg=re.sub(re.escape(start)+r'.*?'+re.escape(end)+r'\s*','',cfg,flags=re.S)
text=re.sub(r'(?m)^#include "tekken6_practice_widget_trace.inc"[^\n]*\n?','',text)
hook='''# BEGIN NATIVE PRACTICE PROMPT FRAME V1
[[midasm_hook]]
address = 0x8236AAAC
name = "MoveNativePracticePromptFrame"
registers = ["r31", "r22", "r23"]
# END NATIVE PRACTICE PROMPT FRAME V1

'''
if '# BEGIN NATIVE PRACTICE PROMPT FRAME V1' not in cfg:
    if cfg.count('[functions]')!=1 or '0x8236aaac' in cfg.lower():raise SystemExit('Unexpected hook layout; no changes made.')
    cfg=cfg.replace('[functions]',hook+'[functions]',1)
elif hook.strip() not in cfg:raise SystemExit('Incomplete prompt hook; no changes made.')
include='#include "tekken6_practice_prompt_widget.inc" // NATIVE PRACTICE PROMPT FRAME V1'
if include not in text:text+='\n'+include+'\n'
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
changes={p:v for p,v in ((source,text),(config,cfg)) if p.read_text(encoding='utf-8-sig')!=v}
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-prompt-widget-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Native practice prompt frame fix installed. Rebuild and package next.')
