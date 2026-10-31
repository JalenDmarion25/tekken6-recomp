from pathlib import Path
import datetime,re,shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp';config=root/'tekken6_config.toml';layout=root/'src/tekken6_native_hud_layout.inc'
if not (root/'src/tekken6_practice_widget_trace.inc').is_file():raise SystemExit('Extract the complete ZIP first. No files changed.')
text=source.read_text(encoding='utf-8-sig');cfg=config.read_text(encoding='utf-8-sig');hud=layout.read_text(encoding='utf-8-sig')
legacy={
 'TraceNativePracticeHudObject':0x82367214,'TraceNativePracticeHudAnimations':0x82463574,
 'BeginNativePracticeHudNode':0x8254AF5C,'InspectNativePracticeHudNode':0x8254AF68,
 'TraceNativePracticeHudScene':0x8256B7F4,'RepositionNativePracticeHudPrompts':0x8256B7F4,
 'RepositionNativePracticeHudPromptBeforeDraw':None,'AdjustNativePracticePromptCoordinates':0x8256C8CC,
}
blocks=re.compile(r'(?ms)^\[\[midasm_hook\]\].*?(?=^\[|\Z)')
removed=[]
def clean(m):
    b=m.group(0);name=re.search(r'^name\s*=\s*"([^"]+)"',b,re.M)
    if not name or name[1] not in legacy:return b
    address=re.search(r'^address\s*=\s*(0x[0-9a-fA-F]+)',b,re.M)
    value=int(address[1],16) if address else None
    expected=legacy[name[1]]
    if (expected is not None and value!=expected) or (expected is None and value not in (0x8256DB40,0x8256DE18)):
        raise SystemExit('Unexpected legacy hook address. No files changed.')
    removed.append(name[1]);return ''
cfg=blocks.sub(clean,cfg)
old_headers=('tekken6_native_hud_trace.inc','tekken6_native_hud_objects_trace.inc','tekken6_native_hud_scene_trace.inc','tekken6_native_hud_prompts.inc','tekken6_native_hud_prompt_render.inc','tekken6_native_hud_prompt_query.inc')
for name in old_headers:text=re.sub(r'(?m)^#include "'+re.escape(name)+r'"[^\n]*\n?','',text)
marker='namespace native_hud_node_trace {'
if marker in hud:
    before,tail=hud.split(marker,1)
    if 'void BeginNativePracticeHudNode' not in tail or 'void InspectNativePracticeHudNode' not in tail:raise SystemExit('Unexpected old trace tail. No files changed.')
    hud=before.rstrip()+'\n'
if 'void AdjustNativePracticeHud(' not in hud:raise SystemExit('Combat HUD layout missing. No files changed.')
hooks='''# BEGIN PRACTICE WIDGET DRAW TRACE V1
[[midasm_hook]]
address = 0x8236CE0C
name = "TracePracticeWidgetTextA"
registers = ["r3", "r4", "r5"]

[[midasm_hook]]
address = 0x82367FBC
name = "TracePracticeWidgetTextB"
registers = ["r3", "r4", "r5"]

[[midasm_hook]]
address = 0x8236AAAC
name = "TracePracticeWidgetFrame"
registers = ["r31", "r22", "r23"]

[[midasm_hook]]
address = 0x82367604
name = "TracePracticeWidgetQuad"
registers = ["r3", "r4"]
# END PRACTICE WIDGET DRAW TRACE V1

'''
if '# BEGIN PRACTICE WIDGET DRAW TRACE V1' not in cfg:
    if cfg.count('[functions]')!=1 or any(a.lower() in cfg.lower() for a in ('0x8236CE0C','0x82367FBC','0x8236AAAC','0x82367604')):raise SystemExit('Conflicting widget hooks. No files changed.')
    cfg=cfg.replace('[functions]',hooks+'[functions]',1)
elif hooks.strip() not in cfg:raise SystemExit('Incomplete widget diagnostic. No files changed.')
include='#include "tekken6_practice_widget_trace.inc" // PRACTICE WIDGET DRAW TRACE V1'
if include not in text:text+='\n'+include+'\n'
changes={p:v for p,v in ((source,text),(config,cfg),(layout,hud)) if p.read_text(encoding='utf-8-sig')!=v}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-widget-trace-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Removed legacy hooks:',', '.join(removed) if removed else 'already removed')
print('Read-only widget diagnostic ready; combat HUD layout retained.')
