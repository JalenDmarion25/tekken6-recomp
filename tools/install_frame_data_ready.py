from pathlib import Path
import datetime
import shutil

root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_frame_data_trace.inc'
text=path.read_text(encoding='utf-8-sig')
expected='// FRAME DATA CORROBORATED BASIC ACTION V2\n#pragma once\n#include "tekken6_frame_data_ready_live.inc"\n'
for name in ('measure','live','rules'):
    if not (root/f'src/tekken6_frame_data_ready_{name}.inc').is_file():
        raise SystemExit('Extract the complete ZIP first. No changes made.')
if text==expected:
    print('Corroborated action reader already installed. Rebuild and package next.')
    raise SystemExit(0)
known=(('// FRAME DATA COMMON BASIC ACTION V1','tekken6_frame_data_common_live.inc'),('// FRAME DATA STANCE ACTION BOUNDARY V1','tekken6_frame_data_stance_live.inc'),
       ('// FRAME DATA STANCE EXPANSION V1','tekken6_frame_data_stance_expand_live.inc'))
if not any(marker in text and text.count('#include "'+name+'"')==1 for marker,name in known):
    raise SystemExit('Expected the working stance or stance-expansion engine. No changes made.')
backup=path.with_name(path.name+'.before-ready-action-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path,backup)
path.write_text(expected,encoding='utf-8')
print('Installed corroborated basic-action timing reader. Rebuild and package next.')
