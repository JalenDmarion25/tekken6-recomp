from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_frame_data_trace.inc'
text=path.read_text(encoding='utf-8-sig')
marker='// FRAME DATA BLOCK CLASSIFIER CORRECTION V1'
if marker in text:print('Block-classifier correction already installed.');raise SystemExit(0)
if '// FRAME DATA LIVE PILOT V1' not in text or text.count('#include "tekken6_frame_data_live.inc"')!=1:
    raise SystemExit('Expected live pilot installation; no files changed.')
if not (root/'src/tekken6_frame_data_block_probe.inc').is_file():raise SystemExit('Extract the complete ZIP first.')
backup=path.with_name(path.name+'.before-block-correction-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path,backup)
path.write_text(marker+'\n#pragma once\n#include "tekken6_frame_data_block_probe.inc"\n',encoding='utf-8')
print('Removed false block-advantage classifier. ON BLOCK stays -- pending verified guard states.')
print('Capture starts with an ordinary attack. No shortcut or delay.')
