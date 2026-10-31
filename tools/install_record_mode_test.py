#!/usr/bin/env python3
"""Experimental MODE SELECT row and cleanup for RECORD/PLAYBACK."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root
names=['src/tekken6_quick_select_roster.inc','src/tekken6_quick_select_menu_records.inc','src/tekken6_quick_select_apply.inc','src/tekken6_guest_hooks.cpp'];s={n:(root/n).read_text(encoding='utf-8-sig') for n in names}
if any('RECORD MODE SWITCH TEST V1' in x for x in s.values()):raise SystemExit('Mode switch test already installed or partial; no changes made.')
def sub(n,old,new):
 if s[n].count(old)!=1:raise SystemExit('Unexpected source in '+n+': '+old[:70])
 s[n]=s[n].replace(old,new,1)
r,m,q,c=names
sub(r,'constexpr uint32_t totalCount=recordWeightBase+3*weightModeSize;','''// RECORD MODE SWITCH TEST V1: three mode-choice records per practice mode.
constexpr uint32_t recordModeChoiceBase=recordWeightBase+3*weightModeSize;
constexpr uint32_t totalCount=recordModeChoiceBase+9;''')
sub(m,'const char* label[] = {"Slot 1", "Slot 2", "Slot 3", "Exit RECORD/PLAYBACK"};', '''// RECORD MODE SWITCH TEST V1: retain the existing menu without the opt-in flag.
    const char* modeFlag=std::getenv("TEKKEN6_TEST_RECORD_MODE");
    const bool modeEnabled=modeFlag && std::strcmp(modeFlag,"1")==0;
    const char* label[]={"Slot 1", "Slot 2", "Slot 3", "Exit RECORD/PLAYBACK"};''')
sub(m,'parent[mode],(commandEnabled?5:4)+(weightedEnabled?3:0),root+1,quick,0);','parent[mode],4+(weightedEnabled?3:0),modeEnabled?root+4:root+1,quick,0);')
old='''      for (uint32_t slot=0;slot<4;++slot)
        node(root+1+slot,346,label[slot],root,0,0,
             slot?root+slot:0,slot<3?root+2+slot:0);
      if(commandEnabled) {
        write(base,records+(root+4)*recordSize+24,root+5);
        node(root+5,346,"Opponent Command List",root,0,0,root+4,0);
      }'''
new='''      // RECORD MODE SWITCH TEST V1: mode choices precede the slot actions.
      if(modeEnabled) {
        const uint32_t choices=recordModeChoiceBase+mode*3;
        const char* modeLabels[]={"FREE STYLE", "VS CPU Training", "DEFENSIVE TRAINING"};
        node(root+4,297,"MODE SELECT",root,3,choices,0,root+1);
        for(uint32_t option=0;option<3;++option)
          node(choices+option,346,modeLabels[option],root+4,0,0,
               option?choices+option-1:0,option<2?choices+option+1:0);
        for (uint32_t slot=0;slot<3;++slot)
          node(root+1+slot,346,label[slot],root,0,0,
               slot?root+slot:root+4,slot<2?root+2+slot:0);
      } else {
        for(uint32_t slot=0;slot<4;++slot)
          node(root+1+slot,346,label[slot],root,0,0,
               slot?root+slot:0,slot<3?root+2+slot:0);
      }'''
sub(m,old,new)
sub(m,'const uint32_t tail=root+(commandEnabled?5:4);','const uint32_t tail=root+(modeEnabled?3:4);')
sub(m,'    const bool commandEnabled=false;','    const bool commandEnabled=false; // RECORD MODE SWITCH TEST V1')
# Make the existing atomic the recording state, so a menu action can stop recording.
sub(c,'    static bool recording=false, previousCombo=false;','''    // RECORD MODE SWITCH TEST V1: menu switching can stop the recording safely.
    static bool previousCombo=false;
    bool recording=recordSlotRecording.load(std::memory_order_acquire);''')
needle=''' // RECORD SLOTS MENU TEST V1: custom IDs fall through the native switch safely.
 const char* slots='''
insert=''' // RECORD MODE SWITCH TEST V1: handle new mode choices and native mode selections.
 const char* modeTest=std::getenv("TEKKEN6_TEST_RECORD_MODE");
 if(modeTest && std::strcmp(modeTest,"1")==0) {
   const bool custom=id.u32>=quick_select_roster::recordModeChoiceBase && id.u32<quick_select_roster::recordModeChoiceBase+9;
   const bool native=id.u32==298 || id.u32==299 || id.u32==351 || id.u32==352 || id.u32==383 || id.u32==384;
   if(custom||native) {
     std::lock_guard<std::mutex> lock(mutex);uint8_t* b=memory();const uint32_t c=b?context(b):0;
     if(!c || read(b,c)!=0x8207D3E4u || active() || object.u32!=0x827BF0D0u) return;
     const int prev=selectedRecordSlot.load(std::memory_order_acquire);
     if(prev>=0 && prev<3 && firstPlaybackCount<=1800) {
       recordedSlotCounts[prev]=firstPlaybackCount;
       std::memcpy(recordedSlotSamples[prev],firstPlaybackSamples,firstPlaybackCount*sizeof(uint32_t));
     }
     recordSlotRecording.store(false,std::memory_order_release);
     firstPlaybackState.store(0,std::memory_order_release);
     firstPlaybackCurrent.store(0,std::memory_order_relaxed);
     firstPlaybackPosition=0;weightedPlaybackActive=false;
     selectedRecordSlot.store(-1,std::memory_order_release);
     recordSlotActive.store(false,std::memory_order_release);
     opponentToggleTest.store(false,std::memory_order_release);
     if(custom) {
       const unsigned x=id.u32-quick_select_roster::recordModeChoiceBase, from=x/3, target=x%3;
       // The native list for each mode contains the other two modes.
       const uint32_t nativeIds[3][3]={{0,298,299},{351,0,352},{383,384,0}};
       const uint32_t action=nativeIds[from][target];
       if(std::FILE* f=std::fopen("record-mode-test.txt","a")) {
         std::fprintf(f,"from=%u target=%u native=%u saved_slot=%d samples=%u\\n",from,target,action,prev,firstPlaybackCount);std::fclose(f);
       }
       // Current-mode choice only exits RECORD/PLAYBACK; other choices use the native callback.
       if(action) id.u64=action;
       return;
     }
     if(std::FILE* f=std::fopen("record-mode-test.txt","a")) {
       std::fprintf(f,"native=%u saved_slot=%d samples=%u\\n",id.u32,prev,firstPlaybackCount);std::fclose(f);
     }
   }
 }
 // RECORD SLOTS MENU TEST V1: custom IDs fall through the native switch safely.
 const char* slots='''
sub(q,needle,insert)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for n in names:
 f=root/n;shutil.copy2(f,f.with_name(f.name+'.before-record-mode-'+stamp));f.write_text(s[n],encoding='utf-8',newline='\n')
print('Installed record mode test; backups use .before-record-mode-'+stamp)
