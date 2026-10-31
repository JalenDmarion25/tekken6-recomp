from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
trace=root/'src/tekken6_frame_data_trace.inc';ui=root/'src/tekken6_frame_data_hud.inc'
t=trace.read_text(encoding='utf-8-sig');u=ui.read_text(encoding='utf-8-sig')
marker='// FRAME DATA LIVE PILOT V1'
if marker in t:
    if 'TekkenFrameDataResult()' in u:print('Live pilot already installed.');raise SystemExit(0)
    raise SystemExit('Partial live installation; no files changed.')
if 'FRAME DATA AUTOMATIC DELAY V2' not in t:raise SystemExit('Expected delayed V2 diagnostic; no files changed.')
for name in ('tekken6_frame_data_measure.inc','tekken6_frame_data_live.inc'):
    if not (root/'src'/name).is_file():raise SystemExit('Extract the full ZIP first.')
old='''      // Pending verified native timing fields. Never substitute guessed data.
      ImGui::TextUnformatted("STARTUP       --");
      ImGui::TextUnformatted("ON BLOCK      --");'''
new='''      const uint64_t data=TekkenFrameDataResult();
      const unsigned startup=unsigned(data&0xFFFFu);
      if(startup)ImGui::Text("STARTUP       %uF",startup);
      else ImGui::TextUnformatted("STARTUP       --");
      if(data&(uint64_t(1)<<32))ImGui::Text("ON BLOCK      %+dF",int(int16_t((data>>16)&0xFFFFu)));
      else ImGui::TextUnformatted("ON BLOCK      --");'''
if u.count(old)!=1 or u.count('bool TekkenFrameDataPracticeActive();')!=1:raise SystemExit('Unexpected HUD layout; no files changed.')
u=u.replace(old,new,1).replace('bool TekkenFrameDataPracticeActive();','bool TekkenFrameDataPracticeActive();\nuint64_t TekkenFrameDataResult();',1)
t=marker+'\n#pragma once\n#include "tekken6_frame_data_live.inc"\n'
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in (trace,ui):shutil.copy2(p,p.with_name(p.name+'.before-live-frame-data-'+stamp))
trace.write_text(t,encoding='utf-8');ui.write_text(u,encoding='utf-8')
print('Installed isolated-contact frame-data pilot. Native prompt layout and recording features retained.')
