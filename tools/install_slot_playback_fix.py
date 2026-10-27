#!/usr/bin/env python3
"""Add Select+B playback to the opt-in Record/Playback slots test."""
from pathlib import Path
from datetime import datetime
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
f=a.root/'src/tekken6_guest_hooks.cpp';s=f.read_text(encoding='utf-8-sig')
marker='// BEGIN SLOT PLAYBACK SHORTCUT V1'
if marker in s:raise SystemExit('Playback shortcut is already installed; no changes made.')
if 'RECORD SLOTS MENU TEST V1' not in s or 'BEGIN RECORD PLAYBACK CYCLE V1' not in s:raise SystemExit('The slot menu and recording cycle are required; no changes made.')
needle='''      previousCombo=combo;
      if (recording) {'''
new='''      previousCombo=combo;
      // BEGIN SLOT PLAYBACK SHORTCUT V1
      // Keep Select+X for recording; Select+B switches from rehearsal to playback.
      static bool previousPlayCombo=false;
      const char* slotTest=std::getenv("TEKKEN6_TEST_RECORD_SLOTS");
      const bool playCombo=slotTest && std::strcmp(slotTest,"1")==0 &&
                           (held.u32 & 0x2020u)==0x2020u;
      if (playCombo && !previousPlayCombo && !recording &&
          selectedRecordSlot.load(std::memory_order_acquire)>=0 &&
          firstPlaybackState.load(std::memory_order_acquire)!=1 && firstPlaybackCount>0) {
        opponentToggleTest.store(false,std::memory_order_relaxed);
        firstPlaybackPosition=0;
        firstPlaybackReads.store(0,std::memory_order_relaxed);
        firstPlaybackCurrent.store(0,std::memory_order_relaxed);
        firstPlaybackState.store(1,std::memory_order_release);
        log("slot-play-start",firstPlaybackCount);
      }
      previousPlayCombo=playCombo;
      // END SLOT PLAYBACK SHORTCUT V1
      if (recording) {'''
if s.count(needle)!=1:raise SystemExit('Expected recording logic differs; no changes made.')
out=s.replace(needle,new,1)
backup=f.with_name(f.name+'.before-slot-playback-fix-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));shutil.copy2(f,backup);f.write_text(out,encoding='utf-8',newline='\n');print('Updated:',f);print('Backup:',backup);print('Rebuild and package.')
