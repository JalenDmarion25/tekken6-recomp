#!/usr/bin/env python3
"""Fix experimental record mode's Free Style action and nested Quick Select."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root
names=['src/tekken6_quick_select_roster.inc','src/tekken6_quick_select_menu_records.inc','src/tekken6_quick_select_apply.inc'];s={n:(root/n).read_text(encoding='utf-8-sig') for n in names}
if any('RECORD MODE FIX V1' in v for v in s.values()):raise SystemExit('Mode fix already installed or partial; no changes made.')
def sub(n,old,new):
 if s[n].count(old)!=1:raise SystemExit('Unexpected source in '+n+': '+old[:80])
 s[n]=s[n].replace(old,new,1)
r,m,q=names
sub(r,'constexpr uint32_t totalCount=recordModeChoiceBase+9;','''// RECORD MODE FIX V1: separate Quick Select copies for the Record/Playback panel.
constexpr uint32_t recordQuickBase=recordModeChoiceBase+9;
constexpr uint32_t totalCount=recordQuickBase+3*subtreeSize;''')
sub(m,'node(root+4,297,"Mode Select",root,3,choices,0,root+1);','''// RECORD MODE FIX V1: fourth choice opens an independently linked Quick Select.
        node(root+4,297,"Mode Select",root,4,choices,0,root+1);''')
sub(m,'''option?choices+option-1:0,option<2?choices+option+1:0);
        for (uint32_t slot=0;slot<3;++slot)''','''option?choices+option-1:0,option<2?choices+option+1:recordQuickBase+mode*subtreeSize);
        const uint32_t srcRoot=quickRow+mode*subtreeSize;
        const uint32_t dstRoot=recordQuickBase+mode*subtreeSize;
        for(uint32_t i=0;i<subtreeSize;++i) {
          const uint32_t src=records+(srcRoot+i)*recordSize, dst=records+(dstRoot+i)*recordSize;
          std::memcpy(base+dst,base+src,recordSize);
          std::memcpy(base+texts+(dstRoot+i)*textSize,base+texts+(srcRoot+i)*textSize,textSize);
          write(base,dst,dstRoot+i);write(base,dst+28,(dstRoot+i)*10);
          for(uint32_t offset:{4u,16u,20u,24u}) {
            const uint32_t value=read(base,dst+offset);
            if(value>=srcRoot && value<srcRoot+subtreeSize) write(base,dst+offset,dstRoot+(value-srcRoot));
          }
        }
        write(base,records+dstRoot*recordSize+4,root+4);
        write(base,records+dstRoot*recordSize+20,choices+2);
        write(base,records+dstRoot*recordSize+24,0);
        for (uint32_t slot=0;slot<3;++slot)''')
sub(q,'const uint32_t nativeIds[3][3]={{0,298,299},{351,0,352},{383,384,0}};','''// RECORD MODE FIX V1: re-enter the selected native mode even when it matches the underlying mode.
       const uint32_t nativeIds[3][3]={{351,298,299},{351,298,352},{383,384,299}};''')
sub(q,'''  write(b,records+(505+delta)*96+80,stage);
 }
 needsSync=false''','''  write(b,records+(505+delta)*96+80,stage);
  // RECORD MODE FIX V1: sync the copies used inside Record/Playback.
  const char* modeFlag=std::getenv("TEKKEN6_TEST_RECORD_MODE");
  if(modeFlag && std::strcmp(modeFlag,"1")==0) {
    const uint32_t nested=quick_select_roster::recordQuickBase+mode*quick_select_roster::subtreeSize;
    write(b,records+(nested+1)*96+80,p1);
    write(b,records+(nested+2)*96+80,p2);
    write(b,records+(nested+3)*96+80,stage);
  }
 }
 needsSync=false''')
sub(q,''' uint32_t mode=0;
 if(id.u32==506) mode=0;
 else if(id.u32==506+quick_select_roster::subtreeSize) mode=1;
 else if(id.u32==506+2*quick_select_roster::subtreeSize) mode=2;
 else return;''',''' // RECORD MODE FIX V1: accept Apply from the nested Quick Select copy.
 uint32_t mode=0; bool nestedQuick=false;
 if(id.u32==506) mode=0;
 else if(id.u32==506+quick_select_roster::subtreeSize) mode=1;
 else if(id.u32==506+2*quick_select_roster::subtreeSize) mode=2;
 else if(id.u32>=quick_select_roster::recordQuickBase+4 &&
         id.u32<quick_select_roster::recordQuickBase+3*quick_select_roster::subtreeSize &&
         (id.u32-quick_select_roster::recordQuickBase)%quick_select_roster::subtreeSize==4) {
   const char* flag=std::getenv("TEKKEN6_TEST_RECORD_MODE");
   if(!flag || std::strcmp(flag,"1")!=0) return;
   mode=(id.u32-quick_select_roster::recordQuickBase)/quick_select_roster::subtreeSize;nestedQuick=true;
 } else return;''')
sub(q,''' const uint32_t delta=mode*quick_select_roster::subtreeSize;
 const uint32_t p1=read(b,records+(503+delta)*96+80),p2=read(b,records+(504+delta)*96+80),stage=read(b,records+(505+delta)*96+80);''',''' const uint32_t delta=nestedQuick ? quick_select_roster::recordQuickBase+mode*quick_select_roster::subtreeSize-502 : mode*quick_select_roster::subtreeSize;
 const uint32_t p1=read(b,records+(503+delta)*96+80),p2=read(b,records+(504+delta)*96+80),stage=read(b,records+(505+delta)*96+80);''')
sub(q,''' if(pending.p1>=102||pending.p2>=102||pending.stage>=100){log("invalid-choice");return;}
 phase=1;''',''' if(pending.p1>=102||pending.p2>=102||pending.stage>=100){log("invalid-choice");return;}
 if(nestedQuick) {
   const int prev=selectedRecordSlot.load(std::memory_order_acquire);
   if(prev>=0 && prev<3 && firstPlaybackCount<=1800) {
     recordedSlotCounts[prev]=firstPlaybackCount;
     std::memcpy(recordedSlotSamples[prev],firstPlaybackSamples,firstPlaybackCount*sizeof(uint32_t));
   }
   recordSlotRecording.store(false,std::memory_order_release);
   firstPlaybackState.store(0,std::memory_order_release);firstPlaybackCurrent.store(0,std::memory_order_relaxed);
   firstPlaybackPosition=0;weightedPlaybackActive=false;
   selectedRecordSlot.store(-1,std::memory_order_release);recordSlotActive.store(false,std::memory_order_release);
   opponentToggleTest.store(false,std::memory_order_release);
 }
 phase=1;''')
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for n in names:
 f=root/n;shutil.copy2(f,f.with_name(f.name+'.before-record-mode-fix-'+stamp));f.write_text(s[n],encoding='utf-8',newline='\n')
print('Installed record mode fix. Backups use .before-record-mode-fix-'+stamp)
