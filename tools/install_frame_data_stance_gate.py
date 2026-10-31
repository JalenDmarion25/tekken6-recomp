from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_frame_data_contacts_live.inc';text=path.read_text(encoding='utf-8-sig')
marker='// STANCE ACTION GATE TRACE V1'
if marker in text:print('Stance action gate trace already installed.');raise SystemExit(0)
if not (root/'src/tekken6_frame_data_stance_gate.inc').is_file():raise SystemExit('Extract the complete ZIP first.')
changes=[('#include "tekken6_frame_data_contacts_measure.inc"','#include "tekken6_frame_data_contacts_measure.inc"\n'+marker+'\n#include "tekken6_frame_data_stance_gate.inc"'),
 ('void CaptureTekkenFrameDataCandidates(uint32_t) {','void CaptureTekkenFrameDataCandidates(uint32_t held) {'),
 ('auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;','auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;\n tekken_stance_gate::Capture(b,currentOwner,held);')]
for old,new in changes:
    if text.count(old)!=1:raise SystemExit('Unexpected contact-tracking source layout; no files changed.')
    text=text.replace(old,new,1)
backup=path.with_name(path.name+'.before-stance-gate-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path,backup);path.write_text(text,encoding='utf-8')
print('Installed focused stance gate capture. Current frame-data calculation unchanged.')
