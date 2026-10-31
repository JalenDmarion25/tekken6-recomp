from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_guest_hooks.cpp'
text=path.read_text(encoding='utf-8')
patches=[
 ('    static bool previousCombo=false;\n    bool recording=recordSlotRecording.load(std::memory_order_acquire);',
  '    static bool previousCombo=false;\n    static bool recordWaitingForRelease=false; // RECORD START RELEASE V1\n    bool recording=recordSlotRecording.load(std::memory_order_acquire);\n    if(!recording) recordWaitingForRelease=false;'),
 ('    auto finish=[&](const char *reason) {\n      recording=false;',
  '    auto finish=[&](const char *reason) {\n      recordWaitingForRelease=false;\n      recording=false;'),
 ('          firstPlaybackCount=0; firstPlaybackPosition=0; recording=true;',
  '          firstPlaybackCount=0; firstPlaybackPosition=0; recording=true;\n          recordWaitingForRelease=true; // Ignore the initiating Select+X until both are released.'),
 ('      if (recording) {\n        if (std::chrono::steady_clock::now()-started>=std::chrono::seconds(30)) finish("time-limit");',
  '      if (recording) {\n        if(recordWaitingForRelease) {\n          if((held.u32 & 0x4020u)==0) {\n            recordWaitingForRelease=false;\n            started=std::chrono::steady_clock::now();\n            log("record-input-ready",0);\n          }\n        } else if (std::chrono::steady_clock::now()-started>=std::chrono::seconds(30)) finish("time-limit");'),
]
s=text
for old,new in patches:
 if new in s:continue
 if s.count(old)!=1:raise SystemExit('Unexpected recording source layout; no files changed. Send this output.')
 s=s.replace(old,new,1)
if s==text:print('Recording start release fix already installed and verified.')
else:
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 shutil.copy2(path,path.with_name(path.name+'.before-start-release-'+stamp))
 path.write_text(s,encoding='utf-8')
 print('Installed recording start release fix. Rebuild and package next.')
