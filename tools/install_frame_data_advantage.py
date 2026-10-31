from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
trace=root/'src/tekken6_frame_data_trace.inc';ui=root/'src/tekken6_frame_data_hud.inc'
t=trace.read_text(encoding='utf-8-sig');u=ui.read_text(encoding='utf-8-sig')
marker='// FRAME DATA HIT AND BLOCK ADVANTAGE V1'
if marker in t:
    if 'FRAME ADVANTAGE' in u and 'ON BLOCK' not in u:print('Hit/block advantage already installed.');raise SystemExit(0)
    raise SystemExit('Partial advantage installation; no files changed.')
supported=(('// FRAME DATA VERIFIED STANDING GUARD V1','#include "tekken6_frame_data_guard_live.inc"'),
           ('// FRAME DATA BLOCK CLASSIFIER CORRECTION V1','#include "tekken6_frame_data_block_probe.inc"'))
if not any(a in t and t.count(b)==1 for a,b in supported):
    raise SystemExit('Expected guard-fix or block-response diagnostic installation; no files changed.')
for name in ('tekken6_frame_data_advantage_measure.inc','tekken6_frame_data_advantage_live.inc'):
    if not (root/'src'/name).is_file():raise SystemExit('Extract the complete ZIP first.')
if u.count('"ON BLOCK      %+dF"')!=1 or u.count('"ON BLOCK      --"')!=1:
    raise SystemExit('Unexpected frame-data HUD layout; no files changed.')
u=u.replace('"ON BLOCK      %+dF"','"FRAME ADVANTAGE  %+dF"',1).replace('"ON BLOCK      --"','"FRAME ADVANTAGE  --"',1)
t=marker+'\n#pragma once\n#include "tekken6_frame_data_advantage_live.inc"\n'
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in (trace,ui):shutil.copy2(p,p.with_name(p.name+'.before-hit-block-advantage-'+stamp))
trace.write_text(t,encoding='utf-8');ui.write_text(u,encoding='utf-8')
print('Installed startup and frame advantage for standing guard and normal standing hit.')
