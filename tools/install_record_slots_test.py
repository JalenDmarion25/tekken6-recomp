#!/usr/bin/env python3
"""Opt-in native menu and three in-memory recording slots. Backups support rollback."""
from pathlib import Path
from datetime import datetime
import argparse, shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
root=a.root
names=['src/tekken6_quick_select_roster.inc','src/tekken6_quick_select_menu_records.inc','src/tekken6_quick_select_apply.inc','src/tekken6_guest_hooks.cpp']
files={x:(root/x).read_text(encoding='utf-8-sig') for x in names}
if any('RECORD SLOTS MENU TEST V1' in s for s in files.values()):raise SystemExit('Already installed or partially installed; no changes made.')
def replace(path,old,new):
 s=files[path]
 if s.count(old)!=1:raise SystemExit('Expected source differs: '+path+' : '+old[:80])
 files[path]=s.replace(old,new,1)
r,menu,apply,cpp=names
replace(r,'constexpr uint32_t totalCount=originalTotalCount+2*subtreeSize;', '''// RECORD SLOTS MENU TEST V1: 3 menus, each with 4 action records.
constexpr uint32_t recordSlotBase=originalTotalCount+2*subtreeSize;
constexpr uint32_t recordSlotStride=5;
constexpr uint32_t totalCount=recordSlotBase+3*recordSlotStride;''')
old='''    write(base, records + tails[mode] * recordSize + 24, quickRow + delta);
  }
}'''
new='''    write(base, records + tails[mode] * recordSize + 24, quickRow + delta);
  }
  // RECORD SLOTS MENU TEST V1
  const char* slotsTest=std::getenv("TEKKEN6_TEST_RECORD_SLOTS");
  if (slotsTest && std::strcmp(slotsTest,"1")==0) {
    const uint32_t parent[] = {297,350,382};
    const char* label[] = {"Slot 1", "Slot 2", "Slot 3", "Exit Record/Playback"};
    for (uint32_t mode=0; mode<3; ++mode) {
      const uint32_t root=recordSlotBase+mode*recordSlotStride;
      const uint32_t quick=quickRow+mode*subtreeSize;
      node(root,297,"Record/Playback",parent[mode],4,root+1,quick,0);
      write(base,records+quick*recordSize+24,root);
      write(base,records+parent[mode]*recordSize+8,4);
      for (uint32_t slot=0;slot<4;++slot)
        node(root+1+slot,346,label[slot],root,0,0,
             slot?root+slot:0,slot<3?root+2+slot:0);
    }
  }
}'''
replace(menu,old,new)
replace(cpp,'std::atomic<bool> opponentToggleTest{false};','''std::atomic<bool> opponentToggleTest{false};
// RECORD SLOTS MENU TEST V1: gameplay updates stop while the practice menu is open.
uint32_t recordedSlotSamples[3][1800] = {};
unsigned recordedSlotCounts[3] = {};
std::atomic<int> selectedRecordSlot{-1};
std::atomic<bool> recordSlotActive{false};
std::atomic<bool> recordSlotRecording{false};''')
replace(cpp,'      recording=false;\n      // Retain the native Controller setting until the menu is opened again.','      recording=false;\n      recordSlotRecording.store(false,std::memory_order_release);\n      // Retain the native Controller setting until the menu is opened again.')
replace(cpp,'firstPlaybackCount=0; firstPlaybackPosition=0; recording=true;','firstPlaybackCount=0; firstPlaybackPosition=0; recording=true;\n          recordSlotRecording.store(true,std::memory_order_release);')
replace(cpp, '    if (!valid) {\n      if (recording) finish("practice-ended");', '''    if (!valid) {
      // RECORD SLOTS MENU TEST V1: detach when the practice owner goes away.
      if (recording) finish("practice-ended");
      if (const char* slotTest=std::getenv("TEKKEN6_TEST_RECORD_SLOTS"); slotTest && std::strcmp(slotTest,"1")==0) {
        const int previous=selectedRecordSlot.exchange(-1,std::memory_order_acq_rel);
        if(previous>=0 && previous<3 && firstPlaybackCount<=1800) {
          recordedSlotCounts[previous]=firstPlaybackCount;
          std::memcpy(recordedSlotSamples[previous],firstPlaybackSamples,firstPlaybackCount*sizeof(uint32_t));
        }
        recordSlotActive.store(false,std::memory_order_release);
      }''')
oldguard='  if (!opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load(std::memory_order_acquire)!=1) return;'
newguard='  if (!opponentToggleTest.load(std::memory_order_relaxed) && firstPlaybackState.load(std::memory_order_acquire)!=1 && !recordSlotActive.load(std::memory_order_acquire)) return;'
replace(cpp,oldguard,newguard)
needle='''void QuickSelectApplyAction(PPCRegister& object,PPCRegister& id) {
 using namespace quick_select_apply_detail;
 uint32_t mode=0;'''
replacement='''void QuickSelectApplyAction(PPCRegister& object,PPCRegister& id) {
 using namespace quick_select_apply_detail;
 // RECORD SLOTS MENU TEST V1: custom IDs fall through the native switch safely.
 const char* slots=std::getenv("TEKKEN6_TEST_RECORD_SLOTS");
 const char* controls=std::getenv("TEKKEN6_TEST_OPPONENT_CONTROL");
 const char* cycle=std::getenv("TEKKEN6_TEST_RECORD_CYCLE");
 if (slots && std::strcmp(slots,"1")==0 && controls && std::strcmp(controls,"1")==0 &&
     cycle && std::strcmp(cycle,"1")==0 && id.u32>=quick_select_roster::recordSlotBase &&
     id.u32<quick_select_roster::recordSlotBase+3*quick_select_roster::recordSlotStride) {
   const unsigned choice=(id.u32-quick_select_roster::recordSlotBase)%quick_select_roster::recordSlotStride;
   if (!choice) return;
   std::lock_guard<std::mutex> lock(mutex);
   uint8_t* b=memory(); if(!b) return;
   const uint32_t c=context(b);
   if(!c || read(b,c)!=0x8207D3E4u || active() || object.u32!=0x827BF0D0u ||
      recordSlotRecording.load(std::memory_order_acquire)) return;
   const int previous=selectedRecordSlot.load(std::memory_order_acquire);
   if(previous>=0 && previous<3 && firstPlaybackCount<=1800) {
     recordedSlotCounts[previous]=firstPlaybackCount;
     std::memcpy(recordedSlotSamples[previous],firstPlaybackSamples,firstPlaybackCount*sizeof(uint32_t));
   }
   firstPlaybackState.store(0,std::memory_order_release);
   firstPlaybackCurrent.store(0,std::memory_order_relaxed);
   firstPlaybackPosition=0;
   if(choice==4) {
     selectedRecordSlot.store(-1,std::memory_order_release);
     recordSlotActive.store(false,std::memory_order_release);
     opponentToggleTest.store(false,std::memory_order_relaxed);
   } else {
     const int chosen=static_cast<int>(choice-1);
     firstPlaybackCount=recordedSlotCounts[chosen];
     std::memcpy(firstPlaybackSamples,recordedSlotSamples[chosen],firstPlaybackCount*sizeof(uint32_t));
     selectedRecordSlot.store(chosen,std::memory_order_release);
     recordSlotActive.store(true,std::memory_order_release);
     opponentToggleTest.store(true,std::memory_order_relaxed);
   }
   if(std::FILE* f=std::fopen("record-slots-test.txt","a")) {
     std::fprintf(f,"choice=%u previous=%d samples=%u\\n",choice,previous,firstPlaybackCount);std::fclose(f);
   }
   return;
 }
 uint32_t mode=0;'''
replace(apply,needle,replacement)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for name in names:
 f=root/name;shutil.copy2(f,f.with_name(f.name+'.before-record-slots-'+stamp));f.write_text(files[name],encoding='utf-8',newline='\n')
print('Installed experimental Record/Playback menu. Backups use suffix .before-record-slots-'+stamp)
