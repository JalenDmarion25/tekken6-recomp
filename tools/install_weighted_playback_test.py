#!/usr/bin/env python3
"""Opt-in three-slot weighted playback with per-slot menu weights."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.root
names=['src/tekken6_quick_select_roster.inc','src/tekken6_quick_select_menu_records.inc','src/tekken6_quick_select_apply.inc','src/tekken6_guest_hooks.cpp'];s={n:(root/n).read_text(encoding='utf-8-sig') for n in names}
if any('WEIGHTED PLAYBACK TEST V1' in x for x in s.values()):raise SystemExit('Already installed or partial; no changes made.')
def replace(n,a,b):
 if s[n].count(a)!=1:raise SystemExit('Expected source differs in '+n+': '+a[:60])
 s[n]=s[n].replace(a,b,1)
r,m,q,c=names
replace(r,'constexpr uint32_t totalCount=recordSlotBase+3*recordSlotStride;', '''// WEIGHTED PLAYBACK TEST V1: three menus, three weights, eleven values each.
constexpr uint32_t recordWeightBase=recordSlotBase+3*recordSlotStride;
constexpr uint32_t weightOptionCount=11, weightGroupSize=12, weightModeSize=36;
constexpr uint32_t totalCount=recordWeightBase+3*weightModeSize;''')
replace(m,'    const bool commandEnabled=commandProbe && std::strcmp(commandProbe,"1")==0;','''    const bool commandEnabled=commandProbe && std::strcmp(commandProbe,"1")==0;
    // WEIGHTED PLAYBACK TEST V1
    const char* weightedTest=std::getenv("TEKKEN6_TEST_WEIGHTED_PLAYBACK");
    const bool weightedEnabled=weightedTest && std::strcmp(weightedTest,"1")==0;''')
replace(m,'parent[mode],commandEnabled?5:4,root+1,quick,0);','parent[mode],(commandEnabled?5:4)+(weightedEnabled?3:0),root+1,quick,0);')
anchor='''        node(root+5,346,"Opponent Command List",root,0,0,root+4,0);
      }
    }
  }
}'''
new='''        node(root+5,346,"Opponent Command List",root,0,0,root+4,0);
      }
      if(weightedEnabled) {
        const uint32_t first=recordWeightBase+mode*weightModeSize;
        const uint32_t tail=root+(commandEnabled?5:4);
        const char* weightLabels[]={"Slot 1 weight", "Slot 2 weight", "Slot 3 weight"};
        const char* values[]={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"};
        write(base,records+tail*recordSize+24,first);
        for(uint32_t slot=0;slot<3;++slot) {
          const uint32_t row=first+slot*weightGroupSize;
          node(row,323,weightLabels[slot],root,weightOptionCount,row+1,
               slot?row-weightGroupSize:tail,slot<2?row+weightGroupSize:0);
          write(base,records+row*recordSize+80,1); // Equal default weights.
          for(uint32_t v=0;v<weightOptionCount;++v)
            node(row+1+v,324,values[v],row,0,0,v?row+v:0,v+1<weightOptionCount?row+v+2:0);
        }
      }
    }
  }
}'''
replace(m,anchor,new)
replace(c,'#include <atomic>\n','#include <atomic>\n#include <random>\n')
replace(c,'std::atomic<bool> recordSlotRecording{false};','''std::atomic<bool> recordSlotRecording{false};
// WEIGHTED PLAYBACK TEST V1
std::atomic<unsigned> recordWeightMenuMode{0};
uint32_t weightedPlaybackSamples[1800]={};
unsigned weightedPlaybackCount=0;
bool weightedPlaybackActive=false;
bool PrepareWeightedPlayback();''')
replace(q,'     selectedRecordSlot.store(chosen,std::memory_order_release);','''     // WEIGHTED PLAYBACK TEST V1: use the weights from this mode's menu tree.
     recordWeightMenuMode.store((id.u32-quick_select_roster::recordSlotBase)/quick_select_roster::recordSlotStride,std::memory_order_release);
     selectedRecordSlot.store(chosen,std::memory_order_release);''')
old='''      if (playCombo && !previousPlayCombo && !recording &&
          selectedRecordSlot.load(std::memory_order_acquire)>=0 &&
          firstPlaybackState.load(std::memory_order_acquire)!=1 && firstPlaybackCount>0) {
        opponentToggleTest.store(false,std::memory_order_relaxed);'''
new='''      // WEIGHTED PLAYBACK TEST V1: select without replacing the active slot's recording.
      const char* weightedEnv=std::getenv("TEKKEN6_TEST_WEIGHTED_PLAYBACK");
      const bool weighted=weightedEnv && std::strcmp(weightedEnv,"1")==0;
      if (playCombo && !previousPlayCombo && !recording &&
          selectedRecordSlot.load(std::memory_order_acquire)>=0 &&
          firstPlaybackState.load(std::memory_order_acquire)!=1 &&
          (weighted ? PrepareWeightedPlayback() : firstPlaybackCount>0)) {
        if(!weighted) weightedPlaybackActive=false;
        opponentToggleTest.store(false,std::memory_order_relaxed);'''
replace(c,old,new)
replace(c,'''        } else if (firstPlaybackPosition<firstPlaybackCount) {
          firstPlaybackCurrent.store(firstPlaybackSamples[firstPlaybackPosition++],std::memory_order_relaxed);''','''        } else if (firstPlaybackPosition<(weightedPlaybackActive?weightedPlaybackCount:firstPlaybackCount)) {
          firstPlaybackCurrent.store(weightedPlaybackActive?weightedPlaybackSamples[firstPlaybackPosition++]:firstPlaybackSamples[firstPlaybackPosition++],std::memory_order_relaxed);''')
# Avoid an unweighted alternate playback on the recording shortcut in this experiment.
replace(c,'''        } else if (firstPlaybackCount) {
          firstPlaybackPosition=0; firstPlaybackReads.store(0);''','''        } else if (firstPlaybackCount && !(std::getenv("TEKKEN6_TEST_WEIGHTED_PLAYBACK") && std::strcmp(std::getenv("TEKKEN6_TEST_WEIGHTED_PLAYBACK"),"1")==0)) {
          weightedPlaybackActive=false;
          firstPlaybackPosition=0; firstPlaybackReads.store(0);''')
anchor='#include "tekken6_quick_select_apply.inc"\n'
impl='''// WEIGHTED PLAYBACK TEST V1
bool PrepareWeightedPlayback() {
 using namespace quick_select_apply_detail;
 std::lock_guard<std::mutex> lock(mutex);
 auto* base=memory();const auto records=practice_rage_menu_detail::menuRecords.load(std::memory_order_acquire);
 const auto c=base?context(base):0;const int selected=selectedRecordSlot.load(std::memory_order_acquire);
 const unsigned mode=recordWeightMenuMode.load(std::memory_order_acquire);
 if(!base||!records||!c||read(base,c)!=0x8207D3E4u||active()||selected<0||selected>=3||mode>=3) return false;
 unsigned weights[3]={},counts[3]={},total=0;
 for(unsigned i=0;i<3;++i) {
   counts[i]=i==static_cast<unsigned>(selected)?firstPlaybackCount:recordedSlotCounts[i];
   const uint32_t row=quick_select_roster::recordWeightBase+mode*quick_select_roster::weightModeSize+i*quick_select_roster::weightGroupSize;
   const uint32_t weight=read(base,records+row*96+80);
   if(counts[i]>0 && counts[i]<=1800 && weight<=10) {weights[i]=weight;total+=weight;}
 }
 if(!total) {if(auto* f=std::fopen("weighted-playback-test.txt","a")){std::fprintf(f,"no-eligible mode=%u\\n",mode);std::fclose(f);}return false;}
 static std::mt19937 rng(static_cast<unsigned>(std::chrono::steady_clock::now().time_since_epoch().count()));
 unsigned draw=std::uniform_int_distribution<unsigned>(0,total-1)(rng),chosen=0;
 for(;chosen<3;++chosen){if(draw<weights[chosen])break;draw-=weights[chosen];}
 const uint32_t* source=chosen==static_cast<unsigned>(selected)?firstPlaybackSamples:recordedSlotSamples[chosen];
 weightedPlaybackCount=counts[chosen];std::memcpy(weightedPlaybackSamples,source,weightedPlaybackCount*sizeof(uint32_t));weightedPlaybackActive=true;
 if(auto* f=std::fopen("weighted-playback-test.txt","a")){std::fprintf(f,"mode=%u selected=%d played=%u weights=%u,%u,%u samples=%u\\n",mode,selected+1,chosen+1,weights[0],weights[1],weights[2],weightedPlaybackCount);std::fclose(f);}
 return true;
}
'''
replace(c,anchor,anchor+impl)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
for n in names:
 f=root/n;shutil.copy2(f,f.with_name(f.name+'.before-weighted-playback-'+stamp));f.write_text(s[n],encoding='utf-8',newline='\n')
print('Installed weighted playback test; backups use .before-weighted-playback-'+stamp)
