from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
app=root/'src/tekken6_app.h';hooks=root/'src/tekken6_guest_hooks.cpp'
a=app.read_text(encoding='utf-8-sig');h=hooks.read_text(encoding='utf-8-sig')
marker='// FRAME DATA HUD V1'
if marker in a or marker in h:
    if marker in a and marker in h:print('Frame data HUD already installed.');raise SystemExit(0)
    raise SystemExit('Partial installation detected; no files changed.')
for name in ('tekken6_frame_data_hud.inc','tekken6_frame_data_trace.inc'):
    if not (root/'src'/name).is_file():raise SystemExit('Extract the full ZIP first.')
def replace_once(text,old,new):
    if text.count(old)!=1:raise SystemExit('Unexpected source layout; no files changed. Missing/ambiguous: '+old[:100])
    return text.replace(old,new,1)
a=replace_once(a,'class Tekken6App final : public rex::ReXApp {',marker+'\n#include "tekken6_frame_data_hud.inc"\nclass Tekken6App final : public rex::ReXApp {')
a=replace_once(a,'if(enabled && std::strcmp(enabled,"1")==0)\n      recordHudFont_', 'if((enabled && std::strcmp(enabled,"1")==0) || std::getenv("TEKKEN6_TEST_FRAME_DATA_HUD"))\n      recordHudFont_')
a=replace_once(a,'    // END RECORD HUD CREATE V1','    // END RECORD HUD CREATE V1\n    const char* frameFlag=std::getenv("TEKKEN6_TEST_FRAME_DATA_HUD");\n    if(drawer && frameFlag && std::strcmp(frameFlag,"1")==0)\n      frameDataHud_=std::make_unique<TekkenFrameDataHud>(drawer,recordHudFont_);')
a=replace_once(a,'  std::unique_ptr<TekkenRecordHud> recordHud_;','  std::unique_ptr<TekkenRecordHud> recordHud_;\n  std::unique_ptr<TekkenFrameDataHud> frameDataHud_;')
# Definition can follow the input hook; declaration belongs before it.
h=replace_once(h,'  practiceHeld.store(held.u32, std::memory_order_relaxed);','  practiceHeld.store(held.u32, std::memory_order_relaxed);\n  CaptureTekkenFrameDataCandidates(held.u32);')
# Existing includes define uint32_t. Insert declaration immediately before the input hook.
needle='void CaptureTekkenFrameDataCandidates(uint32_t held);\n'
input_pos=h.rfind('\nvoid ',0,h.index('  CaptureTekkenFrameDataCandidates(held.u32);'))
if input_pos<0:raise SystemExit('Input function declaration not found; no changes made.')
h=h[:input_pos]+'\n'+needle+h[input_pos:]
h+='\n'+marker+'\n#include "tekken6_frame_data_trace.inc"\n'
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in (app,hooks):shutil.copy2(p,p.with_name(p.name+'.before-frame-data-'+stamp))
app.write_text(a,encoding='utf-8');hooks.write_text(h,encoding='utf-8')
print('Installed frame-data panel and read-only timing capture. Values remain -- pending verification.')
