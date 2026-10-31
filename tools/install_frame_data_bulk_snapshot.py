from pathlib import Path
import datetime
import re
import shutil

root=Path(__file__).resolve().parents[1]
source=root/'src/tekken6_guest_hooks.cpp'
config=root/'tekken6_config.toml'
text=source.read_text(encoding='utf-8-sig')
cfg=config.read_text(encoding='utf-8-sig')
include='#include "tekken6_shared_action_probe.inc" // SHARED ACTION PROBE V1'
if not all((root/'src'/name).is_file() for name in ('tekken6_shared_action_probe.inc','tekken6_bulk_command_snapshot.inc')):
    raise SystemExit('Extract the complete ZIP first. No changes made.')
if 'practiceRageOwner' not in text:
    raise SystemExit('Expected practice owner hooks. No changes made.')
block='''# BEGIN SHARED ACTION PROBE V1
[[midasm_hook]]
address = 0x822871D0
name = "ProbeTekkenNativeSelector"
registers = ["r31", "r3"]

[[midasm_hook]]
address = 0x8228772C
name = "ProbeTekkenNativeScheduler"
registers = ["r31"]

[[midasm_hook]]
address = 0x82288234
name = "ProbeTekkenNativeCommit"
registers = ["r30"]
# END SHARED ACTION PROBE V1

'''
if '# BEGIN SHARED ACTION PROBE V1' in cfg:
    if block.strip() not in cfg:
        raise SystemExit('Incomplete shared probe block. No changes made.')
else:
    if cfg.count('[functions]')!=1:
        raise SystemExit('Unexpected configuration layout. No changes made.')
    addresses=[int(x,0) for x in re.findall(r'(?m)^\s*address\s*=\s*(0x[0-9a-fA-F]+|\d+)',cfg)]
    if any(x in addresses for x in (0x822871D0,0x8228772C,0x82288234)):
        raise SystemExit('A probe address is already hooked. No changes made.')
    cfg=cfg.replace('[functions]',block+'[functions]',1)
if include not in text:text+='\n'+include+'\n'
changes={p:v for p,v in ((source,text),(config,cfg)) if p.read_text(encoding='utf-8-sig')!=v}
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for p in changes:shutil.copy2(p,p.with_name(p.name+'.before-shared-probe-'+stamp))
for p,v in changes.items():p.write_text(v,encoding='utf-8');print('Updated',p.relative_to(root))
print('Bulk command snapshot installed. Existing frame-data engine retained. Rebuild and package next.')
