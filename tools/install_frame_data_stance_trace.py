from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_frame_data_advantage_live.inc'
text=path.read_text(encoding='utf-8-sig')
marker='// STANCE FRAME CAPTURE V1'
if marker in text:print('Stance/string capture already installed.');raise SystemExit(0)
if not (root/'src/tekken6_frame_data_stance_trace.inc').is_file():raise SystemExit('Extract the complete ZIP first.')
changes=[('#include "tekken6_frame_data_advantage_measure.inc"',
          '#include "tekken6_frame_data_advantage_measure.inc"\n'+marker+'\n#include "tekken6_frame_data_stance_trace.inc"'),
         ('void CaptureTekkenFrameDataCandidates(uint32_t) {','void CaptureTekkenFrameDataCandidates(uint32_t held) {'),
         ('auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;',
          'auto* b=runtime?runtime->virtual_membase():nullptr;if(!b)return;\n tekken_stance_trace::Capture(b,currentOwner,held);')]
for a,b in changes:
    if text.count(a)!=1:raise SystemExit('Unexpected live frame-data source layout; no files changed.')
    text=text.replace(a,b,1)
backup=path.with_name(path.name+'.before-stance-capture-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path,backup);path.write_text(text,encoding='utf-8')
print('Installed read-only stance/string capture. Existing frame-data calculation retained.')
