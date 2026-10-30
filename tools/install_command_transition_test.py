#!/usr/bin/env python3
"""Opt-in test: release recording control when opening native opponent commands."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--remove',action='store_true');a=p.parse_args();f=a.root/'src/tekken6_quick_select_apply.inc';s=f.read_text(encoding='utf-8-sig')
b='       // BEGIN COMMAND TRANSITION TEST V1\n';e='       // END COMMAND TRANSITION TEST V1\n'
block='''       // BEGIN COMMAND TRANSITION TEST V1
       // Let the native practice mode regain control while its command list is in use.
       const char* transition=std::getenv("TEKKEN6_TEST_COMMAND_TRANSITION");
       if(transition && std::strcmp(transition,"1")==0) {
         const int previous=selectedRecordSlot.load(std::memory_order_acquire);
         if(previous>=0 && previous<3 && firstPlaybackCount<=1800) {
           recordedSlotCounts[previous]=firstPlaybackCount;
           std::memcpy(recordedSlotSamples[previous],firstPlaybackSamples,firstPlaybackCount*sizeof(uint32_t));
         }
         firstPlaybackState.store(0,std::memory_order_release);
         firstPlaybackCurrent.store(0,std::memory_order_relaxed);
         firstPlaybackPosition=0;
         selectedRecordSlot.store(-1,std::memory_order_release);
         recordSlotActive.store(false,std::memory_order_release);
         opponentToggleTest.store(false,std::memory_order_relaxed);
         if(std::FILE* trace=std::fopen("command-transition-test.txt","a")) {
           std::fprintf(trace,"released slot=%d samples=%u context=%08X\\n",previous,firstPlaybackCount,c);
           std::fclose(trace);
         }
       }
       // END COMMAND TRANSITION TEST V1
'''
if a.remove:
 if s.count(b)!=1 or s.count(e)!=1:raise SystemExit('Transition test missing or inconsistent; no changes made.')
 i=s.index(b);out=s[:i]+s[s.index(e,i)+len(e):]
else:
 if b in s:raise SystemExit('Transition test already installed; no changes made.')
 anchor='''     if(commandProbe && std::strcmp(commandProbe,"1")==0) {
       if(std::FILE* trace=std::fopen("command-menu-probe.txt","a")) {'''
 if s.count(anchor)!=1:raise SystemExit('Expected command menu probe is required; no changes made.')
 out=s.replace(anchor,anchor.replace('       if(std::FILE* trace=',block+'       if(std::FILE* trace='),1)
backup=f.with_name(f.name+'.before-command-transition-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Rebuild and package.')
