from pathlib import Path
import datetime
import shutil

root = Path(__file__).resolve().parents[1]
path = root / 'src/tekken6_frame_data_trace.inc'
text = path.read_text(encoding='utf-8-sig')
marker = '// FRAME DATA STANCE ACTION BOUNDARY V1'
expected = marker + '\n#pragma once\n#include "tekken6_frame_data_stance_live.inc"\n'
for name in ('measure', 'live', 'rules'):
    if not (root / f'src/tekken6_frame_data_stance_{name}.inc').is_file():
        raise SystemExit('Extract the complete ZIP first. No changes made.')
if text == expected:
    print('Stance boundary fix already installed. Rebuild and package next.')
    raise SystemExit(0)
if '// FRAME DATA PER CONTACT V2' not in text or text.count('#include "tekken6_frame_data_contacts_live.inc"') != 1:
    raise SystemExit('Expected the per-contact frame-data installation. No files changed.')
backup = path.with_name(path.name + '.before-stance-boundary-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path, backup)
path.write_text(expected, encoding='utf-8')
print('Installed native stance-boundary calculation. Rebuild and package next.')
