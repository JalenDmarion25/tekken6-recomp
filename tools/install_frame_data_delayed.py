from pathlib import Path
import datetime,shutil
root=Path(__file__).resolve().parents[1]
path=root/'src/tekken6_frame_data_trace.inc'
if not path.is_file():raise SystemExit('Install the frame-data HUD diagnostic first. No files changed.')
text=path.read_text(encoding='utf-8-sig')
marker='// FRAME DATA AUTOMATIC DELAY V2'
if marker in text:print('Delayed diagnostic already installed.');raise SystemExit(0)
old='''  static bool started=false;static unsigned count=0;
  // Explicit arming avoids spending the sample budget on menu confirmations.
  if(!started){if((held&0x8020u)!=0x8020u)return;started=true;}
  if(count>=2400)return;'''
new='''  // FRAME DATA AUTOMATIC DELAY V2: no controller shortcut is read or injected.
  static const auto firstPracticeSample=std::chrono::steady_clock::now();
  if(std::chrono::steady_clock::now()-firstPracticeSample<std::chrono::seconds(30))return;
  static unsigned count=0;
  if(count>=7200)return;'''
changes=[(old,new),('practice-frame-data-trace.txt','practice-frame-data-delayed.txt'),
 ('FRAME DATA CANDIDATES V1:', 'FRAME DATA CANDIDATES V2 (automatic 30-second delay, no trigger chord):'),
 ('count==2400','count==7200')]
for a,b in changes:
    if text.count(a)!=1:raise SystemExit('Unexpected diagnostic source layout; no files changed. Send this output.')
    text=text.replace(a,b,1)
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup=path.with_name(path.name+'.before-delayed-trace-'+stamp)
shutil.copy2(path,backup)
path.write_text(text,encoding='utf-8')
print('Installed automatic delayed capture. No button combination needed.')
print('Backup:',backup)
