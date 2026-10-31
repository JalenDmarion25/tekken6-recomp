from pathlib import Path
import datetime
import shutil

root = Path(__file__).resolve().parents[1]
path = root / 'src/tekken6_frame_data_trace.inc'
text = path.read_text(encoding='utf-8-sig')
expected = '// FRAME DATA STANCE EXPANSION V1\n#pragma once\n#include "tekken6_frame_data_stance_expand_live.inc"\n'
for name in ('measure', 'live', 'rules', 'trace'):
    if not (root / f'src/tekken6_frame_data_stance_expand_{name}.inc').is_file():
        raise SystemExit('Extract the complete ZIP first. No files changed.')
if text == expected:
    print('Stance expansion already installed. Rebuild and package next.')
    raise SystemExit(0)
if '// FRAME DATA STANCE ACTION BOUNDARY V1' not in text or text.count('#include "tekken6_frame_data_stance_live.inc"') != 1:
    raise SystemExit('Expected the working u+4 stance fix. No files changed.')
backup = path.with_name(path.name + '.before-stance-expansion-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path, backup)
path.write_text(expected, encoding='utf-8')
print('Installed bounded direct/shared stance rule reader. Rebuild and package next.')
