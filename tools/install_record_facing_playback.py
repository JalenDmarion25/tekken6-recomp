from pathlib import Path
import datetime
import shutil
import sys
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_guest_hooks.cpp'
text=path.read_text(encoding='utf-8')
patches=[
 ('void TraceTekkenButtons(PPCRegister &object, PPCRegister &buttons)',
  'uint32_t DecodeRecordPlaybackDirection(uint32_t input); // RECORD FACING PLAYBACK V1\nvoid TraceTekkenButtons(PPCRegister &object, PPCRegister &buttons)'),
 ('    buttons.u64=firstPlaybackCurrent.load(std::memory_order_relaxed);',
  '    buttons.u64=DecodeRecordPlaybackDirection(firstPlaybackCurrent.load(std::memory_order_relaxed));'),
 ('bool PrepareWeightedPlayback();',
  'bool PrepareWeightedPlayback();\n#include "tekken6_record_facing.inc" // RECORD FACING PLAYBACK V1'),
 ('        else firstPlaybackSamples[firstPlaybackCount++]=(held.u32 & 0x20u)?0:held.u32;',
  '        else firstPlaybackSamples[firstPlaybackCount++]=EncodeRecordPlaybackDirection((held.u32 & 0x20u)?0:held.u32);'),
]
pending=text
for old,new in patches:
 if new in pending:continue
 if pending.count(old)!=1:raise SystemExit('Unexpected recording source layout; no files changed. Send this output.')
 pending=pending.replace(old,new,1)
if pending==text:
 print('Facing-relative playback already installed and verified.');sys.exit(0)
backup=path.with_name(path.name+'.before-facing-playback-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
shutil.copy2(path,backup)
path.write_text(pending,encoding='utf-8')
print('Installed facing-relative recording and playback. Rebuild and package next.')
