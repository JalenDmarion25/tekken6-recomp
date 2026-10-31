from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_frame_data_trace.inc';text=path.read_text(encoding='utf-8-sig')
marker='// FRAME DATA PER CONTACT V2'
if marker in text:print('Per-contact update already installed.');raise SystemExit(0)
if '// FRAME DATA HIT AND BLOCK ADVANTAGE V1' not in text or text.count('#include "tekken6_frame_data_advantage_live.inc"')!=1:
    raise SystemExit('Expected hit/block advantage installation; no files changed.')
for name in ('tekken6_frame_data_contacts_measure.inc','tekken6_frame_data_contacts_live.inc'):
    if not (root/'src'/name).is_file():raise SystemExit('Extract the complete ZIP first.')
backup=path.with_name(path.name+'.before-per-contact-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path,backup)
path.write_text(marker+'\n#pragma once\n#include "tekken6_frame_data_contacts_live.inc"\n',encoding='utf-8')
print('Installed per-contact string tracking. Unsupported stance recovery displays --; small metadata capture enabled.')
